from app import app

def test_01_customer_portal_loads():
    """Verify that the customer portal route loads successfully."""
    print("\n--- Customer Portal Test ---")
    client = app.test_client()
    response = client.get('/customer')
    assert response.status_code == 200
    print("PASS")


def test_02_manager_login_page_loads():
    """Verify that the manager login page loads successfully."""
    print("\n--- Manager Login Page Test ---")
    client = app.test_client()
    response = client.get('/manager-login')
    assert response.status_code == 200
    print("PASS")


def test_03_manager_dashboard_auth_redirect():
    """Verify that accessing /manager without a session redirects to the login page."""
    print("\n--- Manager Auth Protection Test ---")
    client = app.test_client()
    response = client.get('/manager', follow_redirects=False)
    assert response.status_code == 302
    assert '/manager-login' in response.headers.get('Location', '')
    print("PASS")


def test_04_manager_overview_gui_loads():
    """Verify that the Manager Overview dashboard loads successfully when authenticated."""
    print("\n--- Manager Overview GUI Test ---")
    client = app.test_client()
    # Simulate an active manager login session
    with client.session_transaction() as sess:
        sess["manager_logged_in"] = True
        
    response = client.get('/manager')
    assert response.status_code == 200
    print("PASS")


def test_05_manager_resolve_action():
    """Verify that triggering the manager resolution route processes correctly when authenticated."""
    print("\n--- Manager Resolve Action Test ---")
    client = app.test_client()
    # Simulate an active manager login session
    with client.session_transaction() as sess:
        sess["manager_logged_in"] = True
        
    # Matches the exact route in app.py: /manager/resolve/<complaint_id>
    response = client.post('/manager/resolve/cmp_0001', follow_redirects=True)
    assert response.status_code in [200, 302]
    print("PASS")


if __name__ == "__main__":
    test_01_customer_portal_loads()
    test_02_manager_login_page_loads()
    test_03_manager_dashboard_auth_redirect()
    test_04_manager_overview_gui_loads()
    test_05_manager_resolve_action()