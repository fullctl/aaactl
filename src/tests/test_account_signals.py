def test_generate_api_key(db, account_objects):
    assert account_objects.user.key_set.count() == 1
    assert account_objects.user.key_set.first().managed == False


def test_set_initial_permissions(db, account_objects):
    perms = account_objects.perms
    assert perms.check("user.{}".format(account_objects.user.id), "crud")


def test_create_personal_org(db, account_objects):
    assert account_objects.user.personal_org

def test_create_user_config(db, account_objects):
    assert account_objects.user.usercfg
