import datetime
import logging
import socket

from config import GDL90_RECV_PORT
from gps import Base_GPS, GPS_Data
import gdl90.decoder


# Maximum number of bytes to digest per line (I believe...)
GDL90_RECV_MAXSIZE=9000

class GDL90_Client(Base_GPS):

    def setup(self):
        self.start_datetime = datetime.datetime.combine(
            datetime.date.today(),
            datetime.time(0, 0, 0),
        )

        self.gdl_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.gdl_socket.bind(('', GDL90_RECV_PORT))

        logging.info("Started listening for GDL90 data")


    def loop(self):

        decoder = gdl90.decoder.Decoder()
        logging.info("Waiting for GDL90 data")

        while True:
            (data, dataSrc) = self.gdl_socket.recvfrom(GDL90_RECV_MAXSIZE)
            message_decoded = decoder.addBytes(data)

            #logging.info("Bytes received - message decoded? {}".format(message_decoded))

            if message_decoded == 11:
                if decoder.fix:
                    # Message #11 is processed last, so let's try to send a message
                    # when we receive all the info we need from the GDL90 pipe

                    self.gps_data = GPS_Data(
                        fix = decoder.fix,
                        latitude = decoder.latitude,
                        longitude = decoder.longitude,
                        altitude = decoder.altitude,
                        course = decoder.course,
                        speed = decoder.speed,
                        current_datetime = decoder.current_datetime,
                    )

                    logging.info("Received GDL90 data: {}".format(self.gps_data))
                    if self.scheduler_ready():
                        logging.info("Sending packet")
                        self.send_packet()
                else:
                    logging.info("Received GDL90 data, but no GPS fix")


    def shutdown(self):
        self.gdl_socket.close()
        