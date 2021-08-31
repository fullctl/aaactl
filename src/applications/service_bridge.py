import fullctl.service_bridge.client as client

from account.models import InternalAPIKey


class Bridge(client.Bridge):
    def __init__(self, service, org, user=None):

        api_key = InternalAPIKey.objects.first()

        if not api_key:
            raise KeyError("No internal api key")

        super().__init__(service.api_host, api_key.key, org.slug)

        self.org_id = org.id

        self.user = user
        if user:
            self.user_id = user.id
        else:
            self.user_id = 0

        self.service = service

    def usage(self, product_name):
        # this should stay {org} and not {org_id} so it uses the org slug
        path = self._endpoint("usage", default="usage/{org}")
        data = self.get(path)
        for row in data:
            if row["name"] == product_name:
                return row["units"]
        return None

    def sync_user(self, user_id):
        path = self._endpoint("sync_user", default="aaactl-sync/user/{user}")
        self.put(path)

    def sync_org(self):
        path = self._endpoint("sync_org", default="aaactl-sync/org/{org_id}")
        self.put(path)

    def add_orguser(self, user_id):
        path = self._endpoint("sync_orguser", default="aaactl-sync/orguser/{org_id}")
        self.post(path)

    def del_orguser(self, user_id):
        path = self._endpoint("sync_orguser", default="aaactl-sync/orguser/{org_id}")
        self.post(path)

    def _endpoint(self, name, default=None):
        endpoint = self.service.api_endpoint_set.filter(name=name).first()
        if not endpoint:
            if default:
                path = default
            else:
                raise KeyError(f"No {name} endpoint specified for {self.service.name}")
        else:
            path = endpoint.path

        return path.format(org=self.org, org_id=self.org_id, user=self.user_id)
