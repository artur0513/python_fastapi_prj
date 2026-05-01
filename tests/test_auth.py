def test_signup_success(client, fake_data):
    resp = client.post("/auth/signup", json=fake_data)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == fake_data["email"]
    assert "id" in data


def test_signup_duplicate(client, fake_data):
    client.post("/auth/signup", json=fake_data)
    resp = client.post("/auth/signup", json=fake_data)
    assert resp.status_code == 400
    assert "уже существует" in resp.json()["detail"]


def test_login_success(client, fake_data):
    client.post("/auth/signup", json=fake_data)
    resp = client.post("/auth/login", data={"username": fake_data["email"], "password": fake_data["password"]})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client, fake_data):
    client.post("/auth/signup", json=fake_data)
    resp = client.post("/auth/login", data={"username": fake_data["email"], "password": "wrong"})
    assert resp.status_code == 401
