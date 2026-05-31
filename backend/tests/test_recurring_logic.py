"""
RECURRING PAYMENT LOGIC TESTS

Covers status urgency thresholds and next-payment-date calculation.
"""

from datetime import date, timedelta

from app.services.recurring_payment_logic import (
    calculateNextPaymentDate,
    getDaysUntilPayment,
    getPaymentStatus,
    parse_payment_date,
)


# ─────────────────────────────────────────────────────────────────────────────
# 14. Status urgency — boundary values at 0, 3, 4, 7, 8 days
# ─────────────────────────────────────────────────────────────────────────────
def test_recurring_payment_status_urgency_thresholds_are_correct():
    assert getPaymentStatus(-5) == "overdue"
    assert getPaymentStatus(0)  == "overdue"    # due today → overdue
    assert getPaymentStatus(1)  == "urgent"
    assert getPaymentStatus(3)  == "urgent"     # boundary: still urgent
    assert getPaymentStatus(4)  == "soon"       # boundary: just became soon
    assert getPaymentStatus(7)  == "soon"
    assert getPaymentStatus(8)  == "safe"
    assert getPaymentStatus(30) == "safe"


# ─────────────────────────────────────────────────────────────────────────────
# 15. calculateNextPaymentDate always returns a date >= today
# ─────────────────────────────────────────────────────────────────────────────
def test_recurring_calculate_next_payment_date_is_always_in_the_future():
    # A payment day from the distant past — next occurrence must be >= today
    next_date_str = calculateNextPaymentDate("2018-03-15")
    next_date = parse_payment_date(next_date_str)

    assert next_date >= date.today()

    # getDaysUntilPayment should be >= 0 for this date
    days = getDaysUntilPayment(next_date_str)
    assert days >= 0


def test_recurring_parse_payment_date_accepts_multiple_formats():
    assert parse_payment_date("2025-05-15") == date(2025, 5, 15)
    assert parse_payment_date("15.05.2025") == date(2025, 5, 15)
    assert parse_payment_date("15/05/2025") == date(2025, 5, 15)
