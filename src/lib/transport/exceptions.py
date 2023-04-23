class InvalidPacketException(Exception):
    "Representa un error al decodificar un paquete."
    pass


class SendingNoneData(Exception):
    "Se trató de enviar un stream de bytes nulo"
    pass


class InvalidAddress(Exception):
    "Se trató de enviar un stream de bytes con una dirección nula"
    pass
