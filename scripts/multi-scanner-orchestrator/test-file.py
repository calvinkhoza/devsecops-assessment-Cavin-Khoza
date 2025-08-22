# Test file to verify the orchestrator works.
# This will trigger Bandit (SQL injection) and Gitleaks (fake secret).

import os

def bad_function(user_input):
    # This is a fake SQL injection vulnerability for Bandit to find.
    query = "SELECT * FROM users WHERE id = " + user_input
    return query

# This is a fake AWS key for Gitleaks to find.
AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'