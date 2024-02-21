import json

from django.contrib.auth import authenticate
from django.urls import reverse

import account.models as models
import account.models.federation as federation_models
from tests.helpers import assert_expected, strip_api_fields


def test_federated_service_urls_list(db, account_objects):
    """
    Tests listing federated service URLs for an organization
    """

    auth_info = federation_models.AuthFederation.create_for_org(
        account_objects.org, user=account_objects.user
    )

    service_id = account_objects.federated_service_support.id

    # Create a test federated service URL for the organization
    test_url = "https://example.com/federated-service"
    account_objects.api_client.post(
        reverse("account_api:org-add-federated-service-url", args=(account_objects.org.slug,)),
        data=json.dumps({"url": test_url, "service": service_id}),
        content_type='application/json'
    )

    response = account_objects.api_client.get(
        reverse("account_api:org-federated-service-urls", args=(account_objects.org.slug,))
    )

    assert response.status_code == 200
    
    result = response.json()["data"]

    assert len(result) == 1

    url = result[0]

    assert url["url"] == test_url
    assert url["service"] == service_id
    assert url["auth"] == auth_info.auth.id

    # assert redirect url set on auth_info.auth
    auth_info.auth.refresh_from_db()
    assert auth_info.auth.application.redirect_uris == f"{test_url}/complete/twentyc/"

    # test unauthenticated user
    response = account_objects.api_client_anon.get(
        reverse("account_api:org-federated-service-urls", args=(account_objects.org.slug,))
    )

    assert response.status_code == 403

def test_federated_service_url_create(db, account_objects):
    """
    Tests creating a new federated service URL for an organization
    """

    federation_models.AuthFederation.create_for_org(
        account_objects.org, user=account_objects.user
    )

    service_id = account_objects.federated_service_support.id

    test_url = "https://example.com/new-federated-service"
    response = account_objects.api_client.post(
        reverse("account_api:org-add-federated-service-url", args=(account_objects.org.slug,)),
        data=json.dumps({"url": test_url, "service": service_id}),
        content_type='application/json'
    )

    assert response.status_code == 200

    result = response.json()["data"][0]

    print("RESULT", result)

    assert result["url"] == test_url
    assert result["service"] == service_id

    # test unauthenticated user
    response = account_objects.api_client_anon.post(
        reverse("account_api:org-add-federated-service-url", args=(account_objects.org.slug,)),
        data=json.dumps({"url": test_url, "service": service_id}),
        content_type='application/json'
    )

    assert response.status_code == 403

def test_federated_auth_retrieve(db, account_objects):
    """
    Tests retrieving AuthFederation details for an organization.
    """
    # First, create a federated auth for the org to retrieve later
    auth_info = federation_models.AuthFederation.create_for_org(
        account_objects.org, user=account_objects.user
    )

    response = account_objects.api_client.get(
        reverse("account_api:org-federated-auth", args=(account_objects.org.slug,))
    )

    assert response.status_code == 200
    result = response.json()["data"][0]
    assert result["id"] == auth_info.auth.id
    assert result["org"] == account_objects.org.id
    assert "client_id" in result
    assert "client_secret" in result

    # assert client secret is hashed

    assert result["client_secret"].startswith("pbkdf2_sha256")

    # test unauthenticated user
    response = account_objects.api_client_anon.get(
        reverse("account_api:org-federated-auth", args=(account_objects.org.slug,))
    )

    assert response.status_code == 403


def test_federated_auth_create(db, account_objects):
    """
    Tests creating AuthFederation for an organization.
    """

    response = account_objects.api_client.post(
        reverse("account_api:org-create-federated-auth", args=(account_objects.org.slug,))
    )

    assert response.status_code == 200
    result = response.json()["data"][0]
    assert "id" in result
    assert result["org"] == account_objects.org.id
    assert "client_id" in result
    assert "client_secret" in result

    # assert client secret is not hashed
    assert not result["client_secret"].startswith("pbkdf2_sha256")

    # test unauthenticated user
    response = account_objects.api_client_anon.post(
        reverse("account_api:org-create-federated-auth", args=(account_objects.org.slug,))
    )

    assert response.status_code == 403

