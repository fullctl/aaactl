class Interface(object):

    id = "interface"
    name = "Interface"

    def get_price(self, product):
        raise NotImplemented()
