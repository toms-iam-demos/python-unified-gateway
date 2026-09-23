"""Pure, deterministic USD reconciliation. No external side effects."""
from hashlib import sha256
import json

RULES_VERSION = 'demo-1'
MAX_CENTS = 100_000_000

def money(value):
    return f'${value / 100:,.2f}'

def reconcile(data):
    def amount(value, name):
        if type(value) is not int or not 0 <= value <= MAX_CENTS:
            raise ValueError(f'{name} must be integer cents between 0 and {MAX_CENTS}.')
        return value
    lines = data.get('expenses')
    if not isinstance(lines, list) or not 1 <= len(lines) <= 100:
        raise ValueError('Provide 1–100 expense lines.')
    if not isinstance(data.get('report_id'), str) or not 1 <= len(data['report_id']) <= 80:
        raise ValueError('A report_id of 1–80 characters is required.')
    if type(data.get('report_revision')) is not int or data['report_revision'] < 1:
        raise ValueError('report_revision must be a positive integer.')
    if data.get('currency') != 'USD':
        raise ValueError('This demo supports USD only; convert currencies explicitly upstream.')
    totals = dict(expense_total_cents=0, employee_paid_cents=0, corporate_card_cents=0, c3_total_cents=0, c4_total_cents=0)
    issues, seen = [], set()
    for line in lines:
        if not isinstance(line, dict): raise ValueError('Expense lines must be objects.')
        key = line.get('expense_id')
        if not isinstance(key, str) or not 1 <= len(key) <= 80: raise ValueError('Each expense needs an ID.')
        if key in seen: raise ValueError('Duplicate expense_id: ' + key)
        seen.add(key)
        claimed = amount(line.get('amount_cents'), 'amount_cents')
        c3 = amount(line.get('c3_cents'), 'c3_cents'); c4 = amount(line.get('c4_cents'), 'c4_cents')
        method = line.get('payment_method')
        if method not in ('employee', 'corporate_card'): raise ValueError('Unknown payment method.')
        receipt = line.get('receipt_total_cents')
        if receipt is not None: amount(receipt, 'receipt_total_cents')
        if receipt is None: issues.append({'code':'receipt_missing','expense_id':key,'message':f'{key}: supporting receipt amount is missing.'})
        elif receipt != claimed: issues.append({'code':'receipt_mismatch','expense_id':key,'message':f'{key}: claim and receipt differ by {money(abs(claimed-receipt))}.'})
        if claimed != c3+c4: issues.append({'code':'allocation_mismatch','expense_id':key,'message':f'{key}: allocation difference is {money(claimed-c3-c4)}.'})
        totals['expense_total_cents'] += claimed
        totals['employee_paid_cents' if method == 'employee' else 'corporate_card_cents'] += claimed
        totals['c3_total_cents'] += c3; totals['c4_total_cents'] += c4
    advance = amount(data.get('advance_cents', 0), 'advance_cents')
    previous = amount(data.get('previously_reimbursed_cents', 0), 'previously_reimbursed_cents')
    balance = totals['employee_paid_cents'] - advance - previous
    digest = sha256(json.dumps({'input':data,'rules':RULES_VERSION},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {**totals, 'report_id':data['report_id'], 'report_revision':data['report_revision'], 'rules_version':RULES_VERSION,
      'calculation_id':'CALC-'+digest[:16], 'input_sha256':digest, 'currency':'USD',
      'allocation_difference_cents':totals['expense_total_cents']-totals['c3_total_cents']-totals['c4_total_cents'],
      'advance_applied_cents':advance,'previously_reimbursed_cents':previous,
      'reimbursement_due_cents':max(balance,0),'employee_return_due_cents':max(-balance,0),
      'calculation_status':'needs_review' if issues else 'balanced', 'issues':issues,'blocking_issue_count':len(issues),
      'ready_for_finance_review':not issues, 'payment_status':'not_initiated',
      'funding_eligibility':'not_verified', 'card_transaction_match':'not_verified',
      'reimbursement_due_display':money(max(balance,0)),
      'allocation_summary':f"C3: {money(totals['c3_total_cents'])}; C4: {money(totals['c4_total_cents'])}",
      'issue_summary':' '.join(i['message'] for i in issues) or 'Arithmetic checks passed. Funding eligibility and card matching require separate review.'}
