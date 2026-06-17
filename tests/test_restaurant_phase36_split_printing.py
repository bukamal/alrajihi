from pathlib import Path


def test_phase36_split_bill_endpoints_and_repository_methods_are_present():
    root = Path(__file__).resolve().parents[1]
    routes = (root / 'alrajhi_server/services/http_routes/restaurant.py').read_text(encoding='utf-8')
    repo = (root / 'alrajhi_server/repositories/restaurant_repository.py').read_text(encoding='utf-8')
    for token in [
        '/restaurant/sessions/<int:session_id>/split_bills',
        '/restaurant/split_bills/<int:split_bill_id>/payments',
        '/restaurant/printers',
        '/restaurant/kitchen/tickets/<int:ticket_id>/print_jobs',
        '/restaurant/print_jobs/<int:job_id>/printed',
    ]:
        assert token in routes
    for token in [
        'def create_split_bills',
        'def list_split_bills',
        'def pay_split_bill',
        'def queue_ticket_print',
        'def mark_print_job_done',
        'restaurant_split_bills',
        'restaurant_print_jobs',
    ]:
        assert token in repo


def test_phase36_client_boundary_exposes_split_and_printing_workflow():
    root = Path(__file__).resolve().parents[1]
    service = (root / 'alrajhi_client/core/services/restaurant_service.py').read_text(encoding='utf-8')
    gateway = (root / 'alrajhi_client/gateways/restaurant_gateway.py').read_text(encoding='utf-8')
    for token in [
        'create_split_bills',
        'list_split_bills',
        'pay_split_bill',
        'list_printers',
        'upsert_printer',
        'queue_ticket_print',
        'mark_print_job_done',
    ]:
        assert token in service
        assert token in gateway
