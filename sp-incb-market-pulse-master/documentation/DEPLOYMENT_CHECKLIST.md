# Oracle Database Integration - Deployment Checklist

## Pre-Deployment Checklist

### For Client (Data Extraction)
- [ ] Python 3.8+ installed
- [ ] Oracle Instant Client installed
- [ ] VPN connection configured and tested
- [ ] Database credentials obtained (host, port, username, password)
- [ ] Schema and table names identified
- [ ] Scripts downloaded from Git repository
- [ ] `setup_extraction.bat` or `setup_extraction.sh` executed successfully
- [ ] Environment variables configured
- [ ] `extract_sample_data.py` script tested
- [ ] Sample data extracted successfully
- [ ] Data files reviewed for accuracy
- [ ] ZIP archive created
- [ ] Sample data shared with development team securely

### For Development Team (Post Data Receipt)
- [ ] Sample data received and reviewed
- [ ] Data structure analyzed
- [ ] Column mappings documented
- [ ] Primary/foreign keys identified
- [ ] Parent-Child ranking logic understood
- [ ] Data models designed (Pydantic)
- [ ] Query patterns planned

### For DevOps Team (Infrastructure)
- [ ] Terraform code reviewed
- [ ] AWS account access verified
- [ ] SSM Parameter Store permissions configured
- [ ] KMS key access verified (for SecureString)
- [ ] Terraform initialized: `terraform init`
- [ ] Terraform plan reviewed: `terraform plan`
- [ ] Terraform applied: `terraform apply`
- [ ] SSM parameters created successfully
- [ ] Placeholder values updated with actual credentials
- [ ] Lambda IAM role has SSM read permissions
- [ ] Lambda IAM role has KMS decrypt permissions
- [ ] Network connectivity planned (VPN, PrivateLink, or Security Group)

---

## Deployment Steps

### Step 1: Client Extraction (Day 1)
```
Timeline: 1-2 hours
Owner: Client with VPN access
```

1. [ ] Connect to VPN
2. [ ] Run setup script
3. [ ] Configure environment variables
4. [ ] Execute extraction script
5. [ ] Verify output files
6. [ ] Create ZIP archive
7. [ ] Share with development team

**Deliverables:**
- `sample_data.zip` containing:
  - `database_info.json`
  - `accessible_tables.json`
  - `{TABLE}_schema.json`
  - `{TABLE}_sample_*.csv`
  - `{TABLE}_sample_*.json`

### Step 2: Data Analysis (Day 2)
```
Timeline: 4-6 hours
Owner: Backend Development Team
```

1. [ ] Extract and review sample data
2. [ ] Document data structure
3. [ ] Identify key columns:
   - [ ] Message ID / Primary Key
   - [ ] CUSIP / Security Identifier
   - [ ] Ticker
   - [ ] Source (Bwic Cover, Market, etc.)
   - [ ] Bias / Rank field
   - [ ] Price fields (Bid, Mid, Ask)
   - [ ] Timestamp fields
4. [ ] Map to SRS requirements
5. [ ] Design data models
6. [ ] Plan ranking algorithm (Rank → Date → Price)
7. [ ] Document findings

**Deliverables:**
- Data model documentation
- Column mapping document
- Algorithm design document

### Step 3: Infrastructure Deployment (Day 3)
```
Timeline: 2-3 hours
Owner: DevOps Team
```

1. [ ] Review Terraform code
2. [ ] Update `variables.tf` if needed
3. [ ] Initialize Terraform:
   ```bash
   cd infra
   terraform init
   ```
4. [ ] Plan deployment:
   ```bash
   terraform plan -var-file=variables-ci.tfvars -out=planfile
   ```
5. [ ] Review plan output
6. [ ] Apply infrastructure:
   ```bash
   terraform apply planfile
   ```
7. [ ] Verify SSM parameters created
8. [ ] Update placeholder values:
   ```bash
   aws ssm put-parameter --name "/sp-incb/ci/market-pulse/oracle/host" \
       --value "actual-host.com" --type "String" --overwrite
   # Repeat for all parameters
   ```
9. [ ] Verify Lambda IAM permissions
10. [ ] Test Lambda can read SSM parameters

**Deliverables:**
- Terraform state file
- SSM parameters populated
- Lambda deployed with correct permissions

### Step 4: Database Connection Testing (Day 4)
```
Timeline: 2-4 hours
Owner: Backend Development Team
```

1. [ ] Deploy test Lambda function
2. [ ] Test SSM parameter retrieval
3. [ ] Test Oracle connection from Lambda
4. [ ] Test basic query execution
5. [ ] Test schema inspection
6. [ ] Verify data retrieval
7. [ ] Document connection parameters
8. [ ] Handle errors gracefully

**Test Script:**
```python
from src.main.db_config import OracleDatabase

def test_connection():
    try:
        with OracleDatabase() as db:
            # Test connection
            print("✓ Connected to Oracle")
            
            # Test schema retrieval
            schema = db.get_table_schema('YOUR_TABLE')
            print(f"✓ Retrieved schema: {len(schema)} columns")
            
            # Test data query
            query = "SELECT * FROM YOUR_TABLE WHERE ROWNUM <= 10"
            columns, rows = db.execute_query(query)
            print(f"✓ Retrieved data: {len(rows)} rows")
            
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
```

**Deliverables:**
- Working database connection
- Test results documented
- Connection troubleshooting guide

---

## Post-Deployment Verification

### Functional Tests
- [ ] Lambda can read credentials from SSM
- [ ] Lambda can connect to Oracle database
- [ ] Lambda can execute queries successfully
- [ ] Lambda can retrieve sample data
- [ ] Lambda handles connection errors gracefully
- [ ] Lambda logs properly to CloudWatch

### Security Tests
- [ ] SSM parameters are encrypted (SecureString)
- [ ] Lambda has minimal required permissions
- [ ] No credentials in code or logs
- [ ] KMS encryption working
- [ ] IAM roles follow least privilege

### Performance Tests
- [ ] Connection time < 3 seconds
- [ ] Query execution time acceptable
- [ ] Lambda timeout sufficient
- [ ] Memory allocation appropriate

---

## Rollback Plan

### If Deployment Fails:

1. **Terraform Rollback:**
   ```bash
   terraform destroy -var-file=variables-ci.tfvars
   ```

2. **SSM Parameter Cleanup:**
   ```bash
   aws ssm delete-parameters --names \
       "/sp-incb/ci/market-pulse/oracle/host" \
       "/sp-incb/ci/market-pulse/oracle/port" \
       # ... all parameters
   ```

3. **Lambda Restore:**
   - Deploy previous version
   - Remove database connection code

---

## Success Criteria

### Must Have ✅
- [ ] Client successfully extracted sample data
- [ ] Development team received and analyzed data
- [ ] Terraform deployed without errors
- [ ] SSM parameters populated with actual credentials
- [ ] Lambda IAM permissions configured correctly
- [ ] Lambda can connect to Oracle database
- [ ] Lambda can execute basic queries
- [ ] Sample data matches Oracle source

### Nice to Have 🎯
- [ ] Automated testing pipeline
- [ ] Connection pooling configured
- [ ] Query performance optimized
- [ ] Error monitoring set up
- [ ] Documentation complete

---

## Known Issues & Limitations

### Current Limitations:
1. **VPN/Network:** Lambda needs VPC configuration or VPN/PrivateLink to reach Oracle
2. **Oracle Client:** Lambda layer may be needed for Oracle Instant Client libraries
3. **Connection Pooling:** Not implemented yet (will be added in next iteration)
4. **Retry Logic:** Basic error handling only (enhanced retry coming)

### Future Enhancements:
1. Connection pooling for better performance
2. Query result caching
3. Automatic credential rotation
4. Enhanced monitoring and alerting
5. Query performance optimization

---

## Support & Escalation

### Issue Escalation Path:

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| Client extraction issues | Client IT Support | 4 hours |
| Terraform/AWS issues | DevOps Team | 2 hours |
| Database connectivity | Database Admin Team | 4 hours |
| Application logic | Backend Development Team | 1 business day |

### Emergency Contacts:
- **DevOps Lead:** [Contact Info]
- **Backend Lead:** [Contact Info]
- **Database Admin:** [Contact Info]

---

## Timeline Summary

| Day | Phase | Owner | Duration |
|-----|-------|-------|----------|
| 1 | Data Extraction | Client | 1-2 hours |
| 2 | Data Analysis | Dev Team | 4-6 hours |
| 3 | Infrastructure | DevOps | 2-3 hours |
| 4 | Connection Testing | Dev Team | 2-4 hours |
| **Total** | **End-to-End** | **Multiple** | **~2-3 days** |

---

## Sign-Off

### Client Team
- [ ] Data extraction completed
- [ ] Sample data shared
- **Name:** ________________
- **Date:** ________________

### Development Team
- [ ] Data analysis completed
- [ ] Models designed
- **Name:** ________________
- **Date:** ________________

### DevOps Team
- [ ] Infrastructure deployed
- [ ] Credentials configured
- **Name:** ________________
- **Date:** ________________

### Project Manager
- [ ] All deliverables received
- [ ] Success criteria met
- **Name:** ________________
- **Date:** ________________

---

**Document Version:** 1.0  
**Last Updated:** January 11, 2026  
**Status:** Ready for Deployment
