import fullctl.service_bridge.client as client

class Bridge(client.Bridge):

    def __init__(self, service, org):

        super().__init__(
            service.api_url,
            org.comm_key,
            org.slug
        )

        self.service = service


    def usage(self, product_name):
        endpoint = self._endpoint("usage")
        if not endpoint:
            raise KeyError(f"No usage endpoint specified for {self.service.name}")
        data = self.get(endpoint.path)
        for row in data:
            if row["name"] == product_name:
                return row["units"]
        return None


    def _endpoint(self, name):
        return self.service.api_endpoint_set.filter(name=name).first()
