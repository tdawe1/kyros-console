# PowerShell script to commit changes and prepare for PR

# Navigate to the project root
Set-Location /home/thomas/kyros-console/kyros-console

# Add all changes
git add .

# Commit the changes
git commit -m "feat: terminal daemon guardrails (localhost, caps, idle timeout)

- Bind server to 127.0.0.1 only for network isolation
- Add 2MB per session byte cap with automatic termination
- Implement 10-minute inactivity timeout with reset on input
- Add session logging with unique correlation IDs
- Enforce non-root process execution for security
- Add uuid dependency for session ID generation

Security improvements:
- Prevents remote access by binding to localhost only
- Limits data transfer to prevent resource exhaustion
- Automatic session cleanup prevents resource leaks
- Audit trail for all terminal sessions
- Process security by preventing root execution"

# Push the branch
git push -u origin feat/terminal-daemon-guardrails

Write-Host "✅ Changes committed and pushed to feat/terminal-daemon-guardrails branch"
Write-Host "📝 Ready to create PR with title: 'feat: terminal daemon guardrails (localhost, caps, idle timeout)'"
