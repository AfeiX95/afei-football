# HTML Dashboard Development Pitfalls

> Hard-won lessons from building interactive football analysis dashboards (Chart.js + vanilla JS).

## 1. Line Ending Mismatch (LF vs CRLF)

**Symptom:** Python `str.replace()` finds 0 matches on Windows files.

**Cause:** Files may have LF (`\n`) or CRLF (`\r\n`) line endings. Python string matching is exact.

**Fix:** Always check actual line endings before string replacement:
```python
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
has_crlf = '\r\n' in content  # Check FIRST
```
Then use matching line endings in old/new strings.

## 2. Variable Scope in Template Literals

**Symptom:** `Cannot read properties of undefined (reading 'toFixed')`

**Cause:** Template literal uses `${variable.toFixed(2)}` but `variable` is not defined as a local variable in that scope.

**Fix:** Define ALL variables used in template literals BEFORE the template:
```javascript
// ❌ BAD: hForm not defined
document.getElementById('x').textContent = `${hForm.toFixed(2)}`;

// ✅ GOOD: define first
let hForm = estimateLambda(h, a).hForm || 0;
document.getElementById('x').textContent = `${hForm.toFixed(2)}`;
```

## 3. Duplicate `let` Declarations

**Symptom:** `SyntaxError: Identifier 'X' has already been declared`

**Cause:** Multiple Python patches each add `let x = ...` without checking if it already exists.

**Fix:** Before adding a variable definition, search for existing declarations:
```python
if 'let hForm' not in html[idx:idx+500]:  # Check nearby scope
    html = html[:insert_point] + 'let hForm = ...;\n' + html[insert_point:]
```

## 4. Chart.js CDN Fails on file:// Protocol

**Symptom:** Dashboard works via `http://localhost` but shows blank page when opened via `file://` or double-click.

**Cause:** `file://` protocol blocks external CDN loads (CORS/security policy).

**Fix:** Embed Chart.js inline:
```bash
curl -sL "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js" -o chart.min.js
```
Then replace CDN `<script src="...">` with inline `<script>CONTENT</script>`.

## 5. Python → HTML Injection: Use Exact String Matching

**Best practice for modifying large HTML files:**
1. Read file, find exact substring to replace
2. Verify with `html.count(old_string)` — must be exactly 1
3. Replace with `html.replace(old_string, new_string, 1)` (limit to 1)
4. Write back, validate JS syntax with `node --check`
5. Test in browser, check console for errors

**Never use regex for HTML modification** — too fragile with escaping.

## 6. `node --check` for JS Syntax Validation

Always validate after modifying JS in HTML:
```python
import subprocess
# Extract script content
script_start = html.find('<script>\n//')
script_end = html.rfind('</script>')
script = html[script_start+8:script_end]
with open('/tmp/check.js', 'w') as f:
    f.write(script)
result = subprocess.run(['node', '--check', '/tmp/check.js'], capture_output=True, text=True)
if result.returncode != 0:
    print(f'Syntax error: {result.stderr[:200]}')
```

## 7. Heredoc Escaping Issues

**Symptom:** Python heredoc (`<< 'PYEOF'`) breaks on backticks, quotes, or special chars.

**Fix:** Use Python script files (`write_file` + `terminal`) instead of inline heredoc for complex replacements. The file approach is always safer.
