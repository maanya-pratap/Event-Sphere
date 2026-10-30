from app.models import User
from tests.conftest import login


def test_participant_can_edit_name_mobile_email(client, db, participant_user):
    login(client, participant_user.email)
    client.post("/participant/profile", data={"name": "Maanya P", "mobile": "9876543210", "email": "new@eventsphere.test"})
    u = User.query.get(participant_user.id)
    assert (u.name, u.mobile, u.email) == ("Maanya P", "9876543210", "new@eventsphere.test")


def test_email_must_be_unique(client, db, participant_user, organiser_user):
    login(client, participant_user.email)
    client.post("/participant/profile", data={"name": "X", "email": organiser_user.email})
    assert User.query.get(participant_user.id).email == "participant@eventsphere.test"


def test_password_change_requires_correct_current_password(client, db, participant_user):
    login(client, participant_user.email)
    client.post("/participant/profile", data={"name": "M", "email": participant_user.email,
                                              "current_password": "wrong", "new_password": "brandnew1"})
    assert User.query.get(participant_user.id).check_password("password123")

    client.post("/participant/profile", data={"name": "M", "email": participant_user.email,
                                              "current_password": "password123", "new_password": "brandnew1"})
    assert User.query.get(participant_user.id).check_password("brandnew1")


def test_organiser_can_edit_society_but_not_email(client, db, organiser_user):
    login(client, organiser_user.email)
    client.post("/organiser/profile", data={"name": "Nistha K", "society_name": "Robotics Club",
                                            "mobile": "9999999999", "email": "hacker@x.com"})
    u = User.query.get(organiser_user.id)
    assert u.society_name == "Robotics Club"
    assert u.email == "organiser@eventsphere.test"


def test_participant_cannot_open_organiser_profile(client, db, participant_user):
    login(client, participant_user.email)
    assert client.get("/organiser/profile").status_code == 403
