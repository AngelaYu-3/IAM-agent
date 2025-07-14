# Tool 2: Risk Pattern Analyzer
from langflow.custom import Component
from langflow.io import MessageTextInput, DataInput, Output
from langflow.schema import Data
import pandas as pd

class RiskPatternTool(Component):
    display_name = "Risk Pattern Analyzer Tool"
    description = "Analyze specific risk patterns in user permissions"
    icon = "search"
    name = "RiskPatternTool"
    
    inputs = [
        MessageTextInput(
            name="username",
            display_name="Username",
            info="Username to analyze for risk patterns",
            tool_mode=True,
        ),
        DataInput(
            name="user_data",
            display_name="User Data",
            info="DataFrame containing all user data",
            input_types=["Data", "DataFrame"],
        ),
    ]
    
    outputs = [
        Output(display_name="Risk Analysis", name="risk_analysis", method="analyze_risk_patterns"),
    ]
    
    def analyze_risk_patterns(self) -> Data:
        """Analyze specific risk patterns in user permissions"""
        try:
            username = self.username.strip()
            df = self.user_data
            
            if not isinstance(df, pd.DataFrame):
                return Data(value={"error": "Expected DataFrame input"})
            
            # Find target user
            target_user = df[df['username'].str.lower() == username.lower()]
            if target_user.empty:
                return Data(value={"error": f"User {username} not found"})
            
            user_info = target_user.iloc[0]
            user_role = user_info['role']
            user_dept = user_info['department']
            user_perms = str(user_info['permissions']).split(',')
            employment_status = user_info['employment_status']
            
            risk_patterns = {
                "username": username,
                "total_permissions": len(user_perms),
                "risk_factors": [],
                "severity_score": 0,
                "risk_categories": []
            }
            
            # Pattern 1: Terminated employee with active permissions
            if employment_status.lower() in ['terminated', 'inactive']:
                risk_patterns["risk_factors"].append({
                    "pattern": "stale_access",
                    "description": f"User is {employment_status} but still has {len(user_perms)} active permissions",
                    "severity": "CRITICAL",
                    "impact": "Terminated employees should have zero access"
                })
                risk_patterns["severity_score"] += 10
                risk_patterns["risk_categories"].append("ACCESS_GOVERNANCE")
            
            # Pattern 2: Cross-department admin access
            cross_dept_admin = []
            dept_keywords = ['engineering', 'finance', 'hr', 'sales', 'marketing', 'it']
            user_dept_keyword = user_dept.lower()
            
            for perm in user_perms:
                perm_lower = perm.lower()
                if 'admin' in perm_lower:
                    for dept_keyword in dept_keywords:
                        if dept_keyword != user_dept_keyword and dept_keyword in perm_lower:
                            cross_dept_admin.append(perm)
            
            if cross_dept_admin:
                risk_patterns["risk_factors"].append({
                    "pattern": "cross_department_admin",
                    "description": f"Has admin access to other departments: {', '.join(cross_dept_admin)}",
                    "severity": "HIGH",
                    "impact": "Cross-department admin access violates principle of least privilege"
                })
                risk_patterns["severity_score"] += 7
                risk_patterns["risk_categories"].append("PRIVILEGE_ESCALATION")
            
            # Pattern 3: Destructive permissions
            destructive_perms = []
            destructive_keywords = ['delete', 'remove', 'destroy', 'drop', 'purge']
            for perm in user_perms:
                for keyword in destructive_keywords:
                    if keyword in perm.lower():
                        destructive_perms.append(perm)
            
            if destructive_perms:
                risk_patterns["risk_factors"].append({
                    "pattern": "destructive_permissions",
                    "description": f"Has destructive capabilities: {', '.join(destructive_perms)}",
                    "severity": "HIGH",
                    "impact": "Destructive permissions can cause irreversible damage"
                })
                risk_patterns["severity_score"] += 6
                risk_patterns["risk_categories"].append("DATA_PROTECTION")
            
            # Pattern 4: System-level access
            system_perms = []
            system_keywords = ['root', 'system', 'admin_all', 'superuser', 'emergency']
            for perm in user_perms:
                for keyword in system_keywords:
                    if keyword in perm.lower():
                        system_perms.append(perm)
            
            if system_perms:
                severity = "CRITICAL" if any(word in perm.lower() for perm in system_perms for word in ['root', 'admin_all']) else "HIGH"
                risk_patterns["risk_factors"].append({
                    "pattern": "system_level_access",
                    "description": f"Has system-level permissions: {', '.join(system_perms)}",
                    "severity": severity,
                    "impact": "System-level access provides extensive control over infrastructure"
                })
                risk_patterns["severity_score"] += 8 if severity == "CRITICAL" else 5
                risk_patterns["risk_categories"].append("SYSTEM_SECURITY")
            
            # Pattern 5: Role-permission mismatch
            junior_indicators = ['junior', 'assistant', 'coordinator', 'intern', 'trainee']
            admin_perms = [p for p in user_perms if 'admin' in p.lower()]
            
            if any(indicator in user_role.lower() for indicator in junior_indicators) and admin_perms:
                risk_patterns["risk_factors"].append({
                    "pattern": "junior_role_admin_access",
                    "description": f"Junior role ({user_role}) has admin permissions: {', '.join(admin_perms)}",
                    "severity": "HIGH",
                    "impact": "Junior roles typically should not have administrative privileges"
                })
                risk_patterns["severity_score"] += 6
                risk_patterns["risk_categories"].append("ROLE_BASED_ACCESS")
            
            # Pattern 6: External user with internal access
            if 'contractor' in user_role.lower() or 'consultant' in user_role.lower():
                internal_admin = [p for p in user_perms if 'admin' in p.lower()]
                if internal_admin:
                    risk_patterns["risk_factors"].append({
                        "pattern": "external_user_internal_access",
                        "description": f"External user ({user_role}) has internal admin access: {', '.join(internal_admin)}",
                        "severity": "HIGH",
                        "impact": "External users should have limited, time-bound access"
                    })
                    risk_patterns["severity_score"] += 7
                    risk_patterns["risk_categories"].append("THIRD_PARTY_RISK")
            
            # Determine overall risk level
            if risk_patterns["severity_score"] >= 15:
                risk_level = "CRITICAL"
            elif risk_patterns["severity_score"] >= 8:
                risk_level = "HIGH"
            elif risk_patterns["severity_score"] >= 4:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            risk_patterns["overall_risk_level"] = risk_level
            risk_patterns["risk_categories"] = list(set(risk_patterns["risk_categories"]))
            
            self.status = f"Analyzed {username} - {risk_level} risk ({len(risk_patterns['risk_factors'])} patterns)"
            return Data(value=risk_patterns)
            
        except Exception as e:
            self.status = f"Risk analysis failed: {str(e)}"
            return Data(value={"error": f"Risk pattern analysis failed: {str(e)}"})