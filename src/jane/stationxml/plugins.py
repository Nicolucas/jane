# -*- coding: utf-8 -*-
import io

from django.contrib.gis.geos.point import Point

import matplotlib
from obspy.station.stationxml import validate_StationXML
import obspy

from jane.documents.plugins import ValidatorPluginPoint, IndexerPluginPoint

# Use antigrain interface which also does not require an open display.
matplotlib.use('agg')


class StationValidatorPlugin(ValidatorPluginPoint):
    name = 'stationxml'
    # The validators must contain a content-type field.
    content_type = "text/xml"
    title = 'StationXML XMLSchema Validator'

    def validate(self, document):
        is_stationxml, error = validate_StationXML(document)
        if not is_stationxml:
            raise ValueError(error)
        return True


class StationIndexerPlugin(IndexerPluginPoint):
    name = 'stationxml'
    title = 'StationXML Indexer'

    @property
    def meta(self):
        """
        This defines which fields can be searched over in the indices.
        """
        return {
            "network": {"type": str},
            "station": {"type": str},
            "location": {"type": str},
            "channel": {"type": str},
            "latitude": {"type": float},
            "longitude": {"type": float},
            "elevation_in_m": {"type": float},
            "depth_in_m": {"type": float},
            "start_date": {"type": obspy.UTCDateTime},
            "end_date": {"type": obspy.UTCDateTime},
            "sample_rate": {"type": float},
            "sensor_type": {"type": str},
        }

    def index(self, document):
        inv = obspy.read_inventory(document, format="stationxml")
        indices = []
        for network in inv:
            for station in network:
                for channel in station:
                    # Plot response.
                    plot = io.BytesIO()
                    channel.plot(min_freq=1E-3, outfile=plot)
                    plot.seek(0)

                    indices.append({
                        "network": network.code,
                        "network_name": network.description,
                        "station": station.code,
                        "station_name": station.description if
                        station.description else station.site.name,
                        "location": channel.location_code,
                        "channel": channel.code,
                        "latitude": channel.latitude,
                        "longitude": channel.longitude,
                        "elevation_in_m": channel.elevation,
                        "depth_in_m": channel.depth,
                        "start_date": str(channel.start_date),
                        "sample_rate": float(channel.sample_rate),
                        "sensor_type": channel.sensor.type if channel.sensor
                        else None,
                        "end_date": str(channel.end_date),
                        "geometry": [Point(channel.longitude,
                                           channel.latitude)],
                        "attachments": {
                            "response": {"content-type": "image/png",
                                         "data": plot.read()}
                        },
                    })

        return indices
