import pytest
import tempfile
from django.core.management import call_command
from django.contrib.auth import get_user_model
from account.models import Organization, OrganizationUser, ManagedPermission
from django_grainy.models import UserPermission

User = get_user_model()

@pytest.mark.django_db
def test_aaactl_import_users():
    # Create a temporary CSV file for testing
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as file:
        file.write('username,email,name,asn,org name\n')
        file.write('testuser,testuser@test.com,Test User,123,Test Org\n')
        csv_file = file.name

    # Call the aaactl_import_users command
    call_command('aaactl_import_users', csv_file, commit=True)

    # Check if the user has been created
    user = User.objects.filter(email='testuser@test.com').first()
    assert user is not None
    assert user.username == 'testuser'

    # Check if the organization has been created
    org = Organization.objects.filter(name='Test Org').first()
    assert org is not None

    # Check if the user has been added to the organization
    org_user = OrganizationUser.objects.filter(user=user, org=org).first()
    assert org_user is not None
    assert org_user.is_default == True

    # Check if the ASN permission has been granted to the organization
    asn_permission = UserPermission.objects.filter(namespace__istartswith='verified.asn.123.')
    assert asn_permission.exists()

    managed_perm = ManagedPermission.objects.filter(namespace='verified.asn.123.imported').first()
    assert managed_perm is not None

    org_managed_perm = org.org_managed_permission_set.filter(managed_permission=managed_perm).first()
    assert org_managed_perm is not None
    assert org_managed_perm.reason == f'Imported from {csv_file}'

@pytest.mark.django_db
def test_aaactl_import_users_missing_fields(caplog):
    # Create a temporary CSV file with missing fields
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as file:
        file.write('username,email,name,org name\n')  # 'asn' field is missing
        file.write('testuser,testuser@test.com,Test User,Test Org\n')
        csv_file = file.name

    # Call the aaactl_import_users command
    call_command('aaactl_import_users', csv_file, commit=True)

    # Check if a ValueError was logged
    assert any('CSV file does not contain all the expected fields' in record.message for record in caplog.records)

@pytest.mark.django_db
def test_aaactl_import_users_duplicate_user():
    # Create a user
    User.objects.create_user(username='testuser', email='testuser@test.com')

    # Create a temporary CSV file with a user that already exists
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as file:
        file.write('username,email,name,asn,org name\n')
        file.write('testuser,testuser@test.com,Test User,123,Test Org\n')
        csv_file = file.name

    # Call the aaactl_import_users command
    call_command('aaactl_import_users', csv_file, commit=True)

    # Check that no additional user has been created
    assert User.objects.filter(email='testuser@test.com').count() == 1

@pytest.mark.django_db
def test_aaactl_import_users_existing_org_and_asn_permission():
    # Create a user with permissions to ASN
    existing_user = User.objects.create_user(username='existinguser', email='existinguser@test.com')
    UserPermission.objects.create(user=existing_user, namespace='verified.asn.123.')

    # Create an organization and add the existing user to it
    existing_org = Organization.objects.create(name='Existing Org')
    OrganizationUser.objects.create(user=existing_user, org=existing_org, is_default=True)

    # Create a temporary CSV file with a new user
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as file:
        file.write('username,email,name,asn,org name\n')
        file.write('newuser,newuser@test.com,New User,123,Existing Org\n')
        csv_file = file.name

    # Call the aaactl_import_users command
    call_command('aaactl_import_users', csv_file, commit=True)

    # Check if the new user has been created and added to the existing organization
    new_user = User.objects.filter(email='newuser@test.com').first()
    assert new_user is not None
    org_user = OrganizationUser.objects.filter(user=new_user, org=existing_org).first()
    assert org_user is not None

@pytest.mark.django_db
def test_aaactl_import_users_existing_org_no_asn_permission():
    # Create an existing organization
    existing_org = Organization.objects.create(name='Existing Org')

    # Create a temporary CSV file with a new user and ASN
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as file:
        file.write('username,email,name,asn,org name\n')
        file.write('newuser,newuser@test.com,New User,123,Existing Org\n')
        csv_file = file.name

    # Call the aaactl_import_users command
    call_command('aaactl_import_users', csv_file, commit=True)

    # Check if the new user has been created and added to the existing organization
    new_user = User.objects.filter(email='newuser@test.com').first()
    assert new_user is not None
    org_user = OrganizationUser.objects.filter(user=new_user, org=existing_org).first()
    assert org_user is not None

    # Check if the ASN permission has been granted to the organization
    asn_permission = UserPermission.objects.filter(namespace__istartswith='verified.asn.123.')
    assert asn_permission.exists()

    managed_perm = ManagedPermission.objects.filter(namespace='verified.asn.123.imported').first()
    assert managed_perm is not None

    org_managed_perm = existing_org.org_managed_permission_set.filter(managed_permission=managed_perm).first()
    assert org_managed_perm is not None
    assert org_managed_perm.reason == f'Imported from {csv_file}'