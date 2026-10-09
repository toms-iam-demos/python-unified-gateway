import copy,json,unittest
from pathlib import Path
from app.core import reconcile
from fastapi.testclient import TestClient
from app.main import app

class ReconciliationTests(unittest.TestCase):
    def setUp(self): self.data=json.loads((Path(__file__).parents[1]/'examples/balanced.json').read_text())
    def test_balanced(self):
        r=reconcile(self.data)
        self.assertEqual((r['expense_total_cents'],r['c3_total_cents'],r['c4_total_cents'],r['reimbursement_due_cents']),(96000,66000,30000,52000))
        self.assertEqual(r['payment_status'],'not_initiated')
    def test_line_gaps_cannot_cancel(self):
        self.data['expenses'][0]['c3_cents']+=3000;self.data['expenses'][1]['c3_cents']-=3000
        r=reconcile(self.data);self.assertEqual(r['allocation_difference_cents'],0);self.assertEqual(r['blocking_issue_count'],2)
    def test_receipt_missing_and_mismatch(self):
        self.data['expenses'][0]['receipt_total_cents']=None;self.data['expenses'][1]['receipt_total_cents']=52000
        self.assertEqual(reconcile(self.data)['blocking_issue_count'],2)
    def test_excess_advance(self):
        self.data['advance_cents']=80000;r=reconcile(self.data)
        self.assertEqual((r['reimbursement_due_cents'],r['employee_return_due_cents']),(0,8000))
    def test_previous_payment(self):
        self.data['previously_reimbursed_cents']=10000;self.assertEqual(reconcile(self.data)['reimbursement_due_cents'],42000)
    def test_deterministic_but_revision_sensitive(self):
        first=reconcile(self.data)['calculation_id'];self.assertEqual(first,reconcile(copy.deepcopy(self.data))['calculation_id'])
        self.data['report_revision']+=1;self.assertNotEqual(first,reconcile(self.data)['calculation_id'])
    def test_invalid_money(self):
        for value in (-1,True,1.5,'100',100000001):
            with self.subTest(value=value):
                self.data['advance_cents']=value
                with self.assertRaises(ValueError):reconcile(self.data)
    def test_duplicate_and_currency(self):
        self.data['expenses'].append(copy.deepcopy(self.data['expenses'][0]))
        with self.assertRaises(ValueError):reconcile(self.data)
        self.data['expenses'].pop();self.data['currency']='EUR'
        with self.assertRaises(ValueError):reconcile(self.data)
    def test_api_validation_and_no_mutation_routes(self):
        client=TestClient(app)
        self.assertEqual(client.post('/api/reconcile',json=self.data).status_code,200)
        self.assertEqual(client.post('/api/reconcile',json=[]).status_code,422)
        self.assertEqual(client.post('/api/reconcile',content=b'x'*131073).status_code,413)
        self.assertEqual(client.delete('/api/reconcile').status_code,405)
        self.assertEqual(client.get('/',headers={'host':'evil.example'}).status_code,400)
        self.assertIn("frame-ancestors 'none'",client.get('/').headers['content-security-policy'])
if __name__=='__main__':unittest.main()
