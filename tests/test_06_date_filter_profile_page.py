"""
Tests for Step 6: Date Filter for Profile Page

Spec: .claude/specs/06-date-filter-profile-page.md

Seed data used (demo@spendly.com / demo123):
  2026-05-01  Food           ₹12.50   Lunch at cafe
  2026-05-03  Transport      ₹45.00   Monthly bus pass
  2026-05-05  Bills          ₹120.00  Electricity bill
  2026-05-07  Health         ₹35.00   Pharmacy
  2026-05-10  Entertainment  ₹18.00   Movie ticket
  2026-05-12  Shopping       ₹65.00   Clothing
  2026-05-14  Other          ₹9.99    Miscellaneous
  2026-05-14  Food           ₹22.75   Groceries
  Total: ₹328.24  (8 expenses)
"""

import pytest
from app import app as flask_app
from database.db import init_db, seed_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    """Create a fresh Flask app configured for testing with a real DB path.

    The seed_db() guard (COUNT(*) > 0) means we rely on the on-disk DB that
    is seeded at application startup via `with app.app_context(): seed_db()`.
    We configure TESTING=True and reuse the default DATABASE path so that the
    already-seeded demo data is available to every test.
    """
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False,
    })
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def client(app):
    """Unauthenticated test client."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Test client already logged in as the demo user."""
    response = client.post(
        '/login',
        data={'email': 'demo@spendly.com', 'password': 'demo123'},
        follow_redirects=False,
    )
    # Confirm login succeeded (redirect to /profile means success)
    assert response.status_code == 302, (
        'Login fixture failed — demo@spendly.com / demo123 was rejected'
    )
    return client


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _html(response) -> str:
    return response.data.decode('utf-8')


# ---------------------------------------------------------------------------
# Test 1: Auth guard
# ---------------------------------------------------------------------------

def test_profile_unauthenticated_redirects_to_login(client):
    """Unauthenticated GET /profile must redirect 302 to /login."""
    response = client.get('/profile')
    assert response.status_code == 302, (
        'Expected 302 redirect for unauthenticated /profile'
    )
    assert '/login' in response.headers['Location'], (
        'Redirect target should be /login'
    )


# ---------------------------------------------------------------------------
# Test 2: No-filter baseline — 200 + all-time total
# ---------------------------------------------------------------------------

def test_profile_no_filter_returns_200(auth_client):
    """GET /profile with no params returns HTTP 200."""
    response = auth_client.get('/profile')
    assert response.status_code == 200, (
        'Expected 200 for /profile with no query params'
    )


def test_profile_no_filter_shows_all_time_total(auth_client):
    """GET /profile with no params shows total ₹328.24 (all 8 seed expenses)."""
    response = auth_client.get('/profile')
    html = _html(response)
    assert '328.24' in html, (
        'Expected all-time total ₹328.24 to appear in unfiltered profile'
    )


def test_profile_no_filter_shows_all_eight_transactions(auth_client):
    """GET /profile with no params shows all 8 seed transactions."""
    response = auth_client.get('/profile')
    html = _html(response)
    # The transaction count stat value "8" must appear on the page
    assert '>8<' in html or '">8</div>' in html or 'value">8' in html or '8' in html, (
        'Expected transaction_count of 8 in unfiltered profile'
    )
    # Verify all individual expense descriptions appear
    assert 'Lunch at cafe' in html
    assert 'Monthly bus pass' in html
    assert 'Electricity bill' in html
    assert 'Pharmacy' in html
    assert 'Movie ticket' in html
    assert 'Clothing' in html
    assert 'Miscellaneous' in html
    assert 'Groceries' in html


# ---------------------------------------------------------------------------
# Test 3: No active badge when unfiltered
# ---------------------------------------------------------------------------

def test_profile_no_filter_no_active_badge(auth_client):
    """'Filtered:' badge must NOT appear when no date filter is active."""
    response = auth_client.get('/profile')
    html = _html(response)
    assert 'Filtered:' not in html, (
        '"Filtered:" badge must not appear when no date filter is active'
    )


# ---------------------------------------------------------------------------
# Test 4: Preset links present regardless of filter state
# ---------------------------------------------------------------------------

def test_profile_preset_links_present_unfiltered(auth_client):
    """Preset links 'This Month', 'Last 3 Months', 'Last 6 Months', 'All Time' must appear."""
    response = auth_client.get('/profile')
    html = _html(response)
    assert 'This Month' in html, 'Expected "This Month" preset link'
    assert 'Last 3 Months' in html, 'Expected "Last 3 Months" preset link'
    assert 'Last 6 Months' in html, 'Expected "Last 6 Months" preset link'
    assert 'All Time' in html, 'Expected "All Time" preset link'


def test_profile_preset_links_present_when_filter_active(auth_client):
    """Preset links must also appear when a custom date filter is active."""
    response = auth_client.get('/profile?date_from=2026-05-01&date_to=2026-05-07')
    html = _html(response)
    assert 'This Month' in html, 'Expected "This Month" preset link with filter active'
    assert 'Last 3 Months' in html, 'Expected "Last 3 Months" preset link with filter active'
    assert 'Last 6 Months' in html, 'Expected "Last 6 Months" preset link with filter active'
    assert 'All Time' in html, 'Expected "All Time" preset link with filter active'


# ---------------------------------------------------------------------------
# Test 5 + 6: Custom date range — correct total and count
# ---------------------------------------------------------------------------

def test_profile_custom_range_returns_200(auth_client):
    """Custom date range request returns HTTP 200."""
    response = auth_client.get('/profile?date_from=2026-05-01&date_to=2026-05-07')
    assert response.status_code == 200, (
        'Expected 200 for /profile with valid custom date range'
    )


def test_profile_custom_range_total_correct(auth_client):
    """?date_from=2026-05-01&date_to=2026-05-07 — total must be ₹212.50."""
    response = auth_client.get('/profile?date_from=2026-05-01&date_to=2026-05-07')
    html = _html(response)
    assert '212.50' in html, (
        'Expected filtered total ₹212.50 for date range 2026-05-01 to 2026-05-07'
    )


def test_profile_custom_range_excludes_out_of_range_expenses(auth_client):
    """Expenses outside the date range must not appear in the filtered view."""
    response = auth_client.get('/profile?date_from=2026-05-01&date_to=2026-05-07')
    html = _html(response)
    # These expenses are outside 2026-05-01 to 2026-05-07
    assert 'Movie ticket' not in html, (
        'May 10 expense should be excluded from 2026-05-01..2026-05-07 range'
    )
    assert 'Clothing' not in html, (
        'May 12 expense should be excluded from 2026-05-01..2026-05-07 range'
    )
    assert 'Miscellaneous' not in html, (
        'May 14 expense should be excluded from 2026-05-01..2026-05-07 range'
    )
    assert 'Groceries' not in html, (
        'May 14 expense should be excluded from 2026-05-01..2026-05-07 range'
    )


def test_profile_custom_range_includes_in_range_expenses(auth_client):
    """Expenses inside the date range must appear in the filtered view."""
    response = auth_client.get('/profile?date_from=2026-05-01&date_to=2026-05-07')
    html = _html(response)
    assert 'Lunch at cafe' in html, 'May 01 expense should be in range'
    assert 'Monthly bus pass' in html, 'May 03 expense should be in range'
    assert 'Electricity bill' in html, 'May 05 expense should be in range'
    assert 'Pharmacy' in html, 'May 07 expense should be in range'


# ---------------------------------------------------------------------------
# Test 7: Active filter badge present when filter is applied
# ---------------------------------------------------------------------------

def test_profile_active_filter_badge_appears(auth_client):
    """'Filtered:' must appear in the response when date_from/date_to are valid."""
    response = auth_client.get('/profile?date_from=2026-05-01&date_to=2026-05-07')
    html = _html(response)
    assert 'Filtered:' in html, (
        '"Filtered:" badge must appear when a valid date filter is active'
    )


def test_profile_active_badge_with_date_from_only(auth_client):
    """'Filtered:' must appear even when only date_from is supplied."""
    response = auth_client.get('/profile?date_from=2026-05-10')
    html = _html(response)
    assert 'Filtered:' in html, (
        '"Filtered:" badge must appear when only date_from is provided'
    )


def test_profile_active_badge_with_date_to_only(auth_client):
    """'Filtered:' must appear even when only date_to is supplied."""
    response = auth_client.get('/profile?date_to=2026-05-03')
    html = _html(response)
    assert 'Filtered:' in html, (
        '"Filtered:" badge must appear when only date_to is provided'
    )


# ---------------------------------------------------------------------------
# Test 8: Clear link present when filter is active
# ---------------------------------------------------------------------------

def test_profile_clear_link_present_when_filter_active(auth_client):
    """A 'Clear' link pointing to /profile must appear when a filter is active."""
    response = auth_client.get('/profile?date_from=2026-05-01&date_to=2026-05-07')
    html = _html(response)
    assert 'Clear' in html, (
        'Expected "Clear" link text when date filter is active'
    )
    # The clear link must point to /profile (unfiltered)
    assert 'href="/profile"' in html, (
        'Clear link must point to /profile with no query params'
    )


# ---------------------------------------------------------------------------
# Test 9: Only date_from supplied
# ---------------------------------------------------------------------------

def test_profile_only_date_from_returns_200(auth_client):
    """GET /profile?date_from=2026-05-10 returns HTTP 200."""
    response = auth_client.get('/profile?date_from=2026-05-10')
    assert response.status_code == 200


def test_profile_only_date_from_shows_correct_expenses(auth_client):
    """?date_from=2026-05-10 shows only the 4 expenses on/after May 10."""
    response = auth_client.get('/profile?date_from=2026-05-10')
    html = _html(response)
    # Expenses on/after May 10 must appear
    assert 'Movie ticket' in html, 'May 10 expense must be included'
    assert 'Clothing' in html, 'May 12 expense must be included'
    assert 'Miscellaneous' in html, 'May 14 expense (Other) must be included'
    assert 'Groceries' in html, 'May 14 expense (Food) must be included'
    # Expenses before May 10 must not appear
    assert 'Lunch at cafe' not in html, 'May 01 expense must be excluded'
    assert 'Monthly bus pass' not in html, 'May 03 expense must be excluded'
    assert 'Electricity bill' not in html, 'May 05 expense must be excluded'
    assert 'Pharmacy' not in html, 'May 07 expense must be excluded'


# ---------------------------------------------------------------------------
# Test 10: Only date_to supplied
# ---------------------------------------------------------------------------

def test_profile_only_date_to_returns_200(auth_client):
    """GET /profile?date_to=2026-05-03 returns HTTP 200."""
    response = auth_client.get('/profile?date_to=2026-05-03')
    assert response.status_code == 200


def test_profile_only_date_to_shows_correct_expenses(auth_client):
    """?date_to=2026-05-03 shows only the 2 expenses on/before May 3."""
    response = auth_client.get('/profile?date_to=2026-05-03')
    html = _html(response)
    # Expenses on/before May 3 must appear
    assert 'Lunch at cafe' in html, 'May 01 expense must be included'
    assert 'Monthly bus pass' in html, 'May 03 expense must be included'
    # Expenses after May 3 must not appear
    assert 'Electricity bill' not in html, 'May 05 expense must be excluded'
    assert 'Pharmacy' not in html, 'May 07 expense must be excluded'
    assert 'Movie ticket' not in html, 'May 10 expense must be excluded'
    assert 'Clothing' not in html, 'May 12 expense must be excluded'
    assert 'Miscellaneous' not in html, 'May 14 expense (Other) must be excluded'
    assert 'Groceries' not in html, 'May 14 expense (Food) must be excluded'


def test_profile_only_date_to_total_correct(auth_client):
    """?date_to=2026-05-03 total must be ₹57.50 (12.50 + 45.00)."""
    response = auth_client.get('/profile?date_to=2026-05-03')
    html = _html(response)
    assert '57.50' in html, (
        'Expected filtered total ₹57.50 for date_to=2026-05-03'
    )


# ---------------------------------------------------------------------------
# Test 11: Inverted range (date_from > date_to)
# ---------------------------------------------------------------------------

def test_profile_inverted_range_returns_200(auth_client):
    """Inverted range must return 200 — no crash."""
    response = auth_client.get(
        '/profile?date_from=2026-05-10&date_to=2026-05-01',
        follow_redirects=True,
    )
    assert response.status_code == 200, (
        'Expected 200 even when date_from > date_to'
    )


def test_profile_inverted_range_flashes_error(auth_client):
    """Inverted range must flash 'Start date must be before end date.'"""
    response = auth_client.get(
        '/profile?date_from=2026-05-10&date_to=2026-05-01',
        follow_redirects=True,
    )
    html = _html(response)
    assert 'Start date must be before end date.' in html, (
        'Expected flash error message for inverted date range'
    )


def test_profile_inverted_range_falls_back_to_all_time(auth_client):
    """Inverted range must fall back to all-time data (₹328.24, 8 expenses)."""
    response = auth_client.get(
        '/profile?date_from=2026-05-10&date_to=2026-05-01',
        follow_redirects=True,
    )
    html = _html(response)
    assert '328.24' in html, (
        'Inverted range must fall back to all-time total ₹328.24'
    )
    # All seed expenses should be visible
    assert 'Lunch at cafe' in html
    assert 'Groceries' in html


def test_profile_inverted_range_no_filter_badge(auth_client):
    """Inverted range must NOT show the 'Filtered:' badge (fallback to unfiltered)."""
    response = auth_client.get(
        '/profile?date_from=2026-05-10&date_to=2026-05-01',
        follow_redirects=True,
    )
    html = _html(response)
    assert 'Filtered:' not in html, (
        '"Filtered:" badge must not appear when date range is inverted'
    )


# ---------------------------------------------------------------------------
# Test 12: Malformed date — no crash, fallback to unfiltered
# ---------------------------------------------------------------------------

def test_profile_malformed_date_from_returns_200(auth_client):
    """Malformed date_from must not crash the app — must return 200."""
    response = auth_client.get('/profile?date_from=not-a-date')
    assert response.status_code == 200, (
        'Expected 200 when date_from is malformed'
    )


def test_profile_malformed_date_from_falls_back_to_all_time(auth_client):
    """Malformed date_from must silently fall back to the unfiltered all-time view."""
    response = auth_client.get('/profile?date_from=not-a-date')
    html = _html(response)
    assert '328.24' in html, (
        'Malformed date_from must fall back to all-time total ₹328.24'
    )


def test_profile_malformed_date_to_returns_200(auth_client):
    """Malformed date_to must not crash the app — must return 200."""
    response = auth_client.get('/profile?date_to=2026/05/01')
    assert response.status_code == 200, (
        'Expected 200 when date_to is malformed (wrong separator)'
    )


def test_profile_malformed_date_to_falls_back_to_all_time(auth_client):
    """Malformed date_to must silently fall back to the unfiltered all-time view."""
    response = auth_client.get('/profile?date_to=2026/05/01')
    html = _html(response)
    assert '328.24' in html, (
        'Malformed date_to must fall back to all-time total ₹328.24'
    )


def test_profile_malformed_date_no_filter_badge(auth_client):
    """'Filtered:' badge must not appear when the date param is malformed."""
    response = auth_client.get('/profile?date_from=not-a-date')
    html = _html(response)
    assert 'Filtered:' not in html, (
        '"Filtered:" must not appear when date_from is malformed'
    )


# ---------------------------------------------------------------------------
# Test 13: Empty result — date range with no matching expenses
# ---------------------------------------------------------------------------

def test_profile_empty_range_returns_200(auth_client):
    """A date range with no matching expenses must return 200."""
    response = auth_client.get('/profile?date_from=2025-01-01&date_to=2025-01-31')
    assert response.status_code == 200, (
        'Expected 200 for a date range with no expenses'
    )


def test_profile_empty_range_shows_zero_total(auth_client):
    """A date range with no matching expenses must show ₹0.00 total."""
    response = auth_client.get('/profile?date_from=2025-01-01&date_to=2025-01-31')
    html = _html(response)
    assert '0.00' in html, (
        'Expected ₹0.00 total when no expenses match the date range'
    )


def test_profile_empty_range_shows_zero_transactions(auth_client):
    """A date range with no matching expenses must show 0 transactions."""
    response = auth_client.get('/profile?date_from=2025-01-01&date_to=2025-01-31')
    html = _html(response)
    # transaction_count of 0 must appear as a stat value
    assert '>0<' in html or '0' in html, (
        'Expected 0 transaction count when no expenses match the date range'
    )


def test_profile_empty_range_no_errors(auth_client):
    """A date range with no matching expenses must not produce a server error."""
    response = auth_client.get('/profile?date_from=2025-01-01&date_to=2025-01-31')
    # Status 200 already asserted above; also verify no error keywords
    html = _html(response)
    assert '500' not in html, 'No internal server error on empty result set'
    assert 'traceback' not in html.lower(), 'No traceback on empty result set'


# ---------------------------------------------------------------------------
# Test 14: All amounts display the ₹ symbol
# ---------------------------------------------------------------------------

def test_profile_amounts_use_rupee_symbol_unfiltered(auth_client):
    """All expense amounts in the unfiltered view must use the ₹ symbol."""
    response = auth_client.get('/profile')
    html = _html(response)
    assert '₹' in html, (
        'Expected ₹ symbol in unfiltered profile amounts'
    )


def test_profile_amounts_use_rupee_symbol_filtered(auth_client):
    """All expense amounts in a filtered view must use the ₹ symbol."""
    response = auth_client.get('/profile?date_from=2026-05-01&date_to=2026-05-07')
    html = _html(response)
    assert '₹' in html, (
        'Expected ₹ symbol in filtered profile amounts'
    )


def test_profile_amounts_use_rupee_symbol_empty_range(auth_client):
    """The ₹0.00 fallback in an empty date range must also use the ₹ symbol."""
    response = auth_client.get('/profile?date_from=2025-01-01&date_to=2025-01-31')
    html = _html(response)
    assert '₹' in html, (
        'Expected ₹ symbol even when the filtered view returns zero results'
    )
