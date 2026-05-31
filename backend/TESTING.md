# FinLit Backend — Test Suite

## Quick start

```bash
# From the backend/ directory
pip install -r requirements.txt
pip install httpx          # async test client (one extra package)

pytest -v                  # run all 32 tests
pytest tests/test_kaspi_parser.py -v   # parser tests only
```

No running MongoDB, Redis, or OpenAI key is required.

---

## Coverage — 32 tests across 8 files

### Kaspi Bank PDF Parser — `tests/test_kaspi_parser.py` (11 tests)

| # | Test name | What it verifies |
|---|-----------|-----------------|
| 1 | `test_parser_amounts_with_spaces_commas_and_currency_are_parsed_correctly` | `parse_amount` handles `12 500,00 ₸`, commas, `тг`, None, empty string |
| 2 | `test_parser_extracts_statement_period_as_iso_dates` | Period "за период с DD.MM.YYYY по DD.MM.YYYY" → ISO dates |
| 3 | `test_parser_returns_none_when_period_line_is_absent` | Graceful `None` when no period line exists |
| 4 | `test_parser_summary_block_extracts_income_and_expense_fields` | Пополнения, Покупки, Переводы, Снятия parsed from summary block |
| 5 | `test_parser_extracts_correct_transaction_count_date_and_amount` | 7 transactions parsed; first has correct date, amount, operation, details |
| 6 | `test_parser_correctly_separates_income_from_expenses_by_sign` | Positive = income (1 txn), negative = expense (6 txns); sums match |
| 7 | `test_finance_calculator_total_expense_matches_transaction_sum` | `calculate_summary` totalExpense == sum of negative-amount transactions |
| 8 | `test_category_manager_without_ai_assigns_expenses_to_prochie_rashody` | When merchant_categories = {}, all purchases land in «Прочие расходы» |
| 9 | `test_parser_handles_garbage_and_empty_lines_without_crashing` | Lorem ipsum / `€€€` / blank lines don't raise; only valid line is parsed |
| 10 | `test_chart_data_builder_aggregates_daily_expenses_by_date` | 31 entries for May; correct per-day expense; income days show 0 |

---

### Balance Service — `tests/test_balance_service.py` (4 tests)

| # | Test name | What it verifies |
|---|-----------|-----------------|
| 11 | `test_balance_unaccounted_expense_is_zero_when_categories_cover_all_expenses` | unaccounted = max(0, …) is clamped at 0 when categories exceed expense |
| 12 | `test_balance_unaccounted_expense_equals_gap_when_categories_are_partial` | Correct positive gap when categories don't cover total expense |
| 13 | `test_balance_calculates_surplus_and_expense_ratio_correctly` | surplus = income − expense; expense_ratio = %; breakdown percentages |
| 14 | `test_balance_expense_ratio_is_zero_when_income_is_zero` | No division-by-zero; ratio = 0 when income = 0 |

---

### Security — `tests/test_security.py` (2 tests)

| # | Test name | What it verifies |
|---|-----------|-----------------|
| 15 | `test_security_password_hash_and_verify_work_correctly` | bcrypt hash format; correct pw → True; wrong pw → False |
| 16 | `test_security_jwt_valid_token_decodes_and_expired_tampered_tokens_return_none` | Valid token → payload["sub"]; expired token → None; tampered token → None |

---

### Recurring Payment Logic — `tests/test_recurring_logic.py` (3 tests)

| # | Test name | What it verifies |
|---|-----------|-----------------|
| 17 | `test_recurring_payment_status_urgency_thresholds_are_correct` | overdue (≤0), urgent (1–3), soon (4–7), safe (≥8) boundary values |
| 18 | `test_recurring_calculate_next_payment_date_is_always_in_the_future` | Next date ≥ today; getDaysUntilPayment ≥ 0 |
| 19 | `test_recurring_parse_payment_date_accepts_multiple_formats` | YYYY-MM-DD, DD.MM.YYYY, DD/MM/YYYY all parse correctly |

---

### API — Auth `tests/test_api_auth.py` (3 tests)

| # | Test name | What it verifies |
|---|-----------|-----------------|
| 20 | `test_register_user_returns_token_and_user_on_happy_path` | POST /api/auth/register → 200, access_token, no hashed_password in response |
| 21 | `test_login_user_returns_access_token_on_valid_credentials` | POST /api/auth/login → 200, access_token |
| 22 | `test_protected_endpoint_returns_401_without_auth_token` | GET /api/auth/me without token → 401 |

---

### API — Reports `tests/test_api_reports.py` (2 tests)

| # | Test name | What it verifies |
|---|-----------|-----------------|
| 23 | `test_create_report_calculates_balance_and_returns_persisted_report` | POST /api/reports → 200, report has correct fields |
| 24 | `test_calculate_balance_preview_returns_surplus_and_expense_ratio` | POST /api/reports/calculate-balance → surplus, expense_ratio, unaccounted_expense |

---

### API — Goals `tests/test_api_goals.py` (2 tests)

| # | Test name | What it verifies |
|---|-----------|-----------------|
| 25 | `test_create_goal_returns_goal_with_progress_percent` | POST /api/goals → 200, progress_percent = 25.0 for 25k/100k |
| 26 | `test_goal_progress_percent_is_capped_at_100_when_overfunded` | progress_percent capped at 100.0 when current > target |

---

### API — Recurring Payments `tests/test_api_recurring.py` (2 tests)

| # | Test name | What it verifies |
|---|-----------|-----------------|
| 27 | `test_create_recurring_payment_returns_payment_with_next_date_and_status` | POST /api/recurring-payments → 200, has nextPaymentDate and valid status |
| 28 | `test_list_recurring_payments_returns_empty_list_when_user_has_none` | GET /api/recurring-payments → 200, [] |

---

### API — Admin `tests/test_api_admin.py` (2 tests)

| # | Test name | What it verifies |
|---|-----------|-----------------|
| 29 | `test_regular_user_gets_403_on_admin_stats_endpoint` | GET /api/admin/stats with role=user → 403 |
| 30 | `test_admin_user_can_access_global_stats` | GET /api/admin/stats with role=admin → 200 |

---

### Pre-existing — AI Context Service `tests/test_ai_context_service.py` (2 tests)

These tests existed before this suite was created and continue to pass.

---

## Infrastructure

- `pytest.ini` — `asyncio_mode = auto` (no `@pytest.mark.asyncio` needed)
- `tests/conftest.py` — shared fixtures: `anon_client`, `user_client`, `admin_client`, `fake_user`, `fake_admin`; `_mock_db_connections` autouse fixture patches MongoDB startup to prevent real connections
- All API tests use `httpx.AsyncClient` with `ASGITransport` (no live server)
- External services mocked: MongoDB (via `unittest.mock.patch` on repo functions), Redis (`get_redis` returns `None` by default), OpenAI (not called — `OPENAI_API_KEY` is empty in tests)
