import io

P = 'frontend/src/App.tsx'
L = io.open(P, encoding='utf-8').read().split('\n')

def find(pattern, start=0):
    for i in range(start, len(L)):
        if L[i].startswith(pattern):
            return i
    raise SystemExit('not found: ' + pattern)

# Locate block boundaries (1-based line numbers from inspection).
i_form = find('function FormPage(')
i_rows = find('const rows = {')
i_format = find('function formatDate(')
i_applicants = find('function ApplicantsPanel(')
i_datapage = find('function DataPage(')
i_referraldetail = find('function ReferralDetail(')
i_planner = find('function Planner(')
i_shell = find('function Shell(')

print('form', i_form + 1, 'rows', i_rows + 1, 'format', i_format + 1,
      'applicants', i_applicants + 1, 'datapage', i_datapage + 1,
      'referraldetail', i_referraldetail + 1, 'planner', i_planner + 1, 'shell', i_shell + 1)

new_forms = io.open('_forms1.txt', encoding='utf-8').read().rstrip('\n').split('\n')
refer_form = io.open('_forms2.txt', encoding='utf-8').read().rstrip('\n').split('\n')
photo_pw = io.open('_forms3.txt', encoding='utf-8').read().rstrip('\n').split('\n')
profile = io.open('_forms4.txt', encoding='utf-8').read().rstrip('\n').split('\n')
manage = io.open('_panels1.txt', encoding='utf-8').read().rstrip('\n').split('\n')
referrals = io.open('_panels3.txt', encoding='utf-8').read().rstrip('\n').split('\n')
myrefs = io.open('_panels4.txt', encoding='utf-8').read().rstrip('\n').split('\n')
refdetail = io.open('_panels5.txt', encoding='utf-8').read().rstrip('\n').split('\n')

# Assemble: replace FormPage..(before `const rows`) with the new forms.
# Keep formatDate/statusTone/NEXT_STATUSES and ApplicantsPanel/ResumeCard/
# ApplicationsPanel intact. Replace DataPage and ReferralDetail entirely.
out = []
out += L[:i_form]
out += new_forms + [''] + refer_form + [''] + photo_pw + [''] + profile + ['']
out += L[i_rows:i_datapage]          # formatDate .. ApplicationsPanel end
out += manage + [''] + referrals + [''] + myrefs + [''] + refdetail + ['']
out += L[i_planner:]                 # Planner, AccessPage, App, Shell
io.open(P, 'w', encoding='utf-8', newline='').write('\n'.join(out))
print('total lines now', len(out))
