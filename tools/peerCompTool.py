# Tool 1: Peer Comparison Tool
from langflow.custom import Component
from langflow.io import MessageTextInput, DataInput, Output
from langflow.schema import Data
import pandas as pd

class PeerComparisonTool(Component):
    display_name = "Peer Comparison Tool"
    description = "Compare user permissions with peers in same role/department"
    icon = "users"
    name = "PeerComparisonTool"
    
    inputs = [
        MessageTextInput(
            name="username",
            display_name="Username",
            info="Username to compare with peers",
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
        Output(display_name="Comparison Result", name="comparison", method="compare_with_peers"),
    ]
    
    def compare_with_peers(self) -> Data:
        """Compare user with peers in same role and department"""
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
            user_dept = user_info['department']
            user_role = user_info['role']
            user_perms = str(user_info['permissions']).split(',')
            
            # Find exact peers (same dept + role)
            exact_peers = df[
                (df['department'] == user_dept) & 
                (df['role'] == user_role) & 
                (df['username'] != username)
            ]
            
            # Find role peers (same role, different dept)
            role_peers = df[
                (df['role'] == user_role) & 
                (df['username'] != username)
            ]
            
            comparison_result = {
                "username": username,
                "department": user_dept,
                "role": user_role,
                "user_permission_count": len(user_perms),
                "exact_peers_found": len(exact_peers),
                "role_peers_found": len(role_peers),
            }
            
            if len(exact_peers) > 0:
                # Analyze exact peers
                peer_perm_counts = []
                common_perms = set()
                all_peer_perms = set()
                
                for _, peer in exact_peers.iterrows():
                    peer_perms = str(peer['permissions']).split(',')
                    peer_perm_counts.append(len(peer_perms))
                    all_peer_perms.update(peer_perms)
                
                # Find permissions only target user has
                user_perm_set = set(user_perms)
                unique_to_user = user_perm_set - all_peer_perms
                missing_from_user = all_peer_perms - user_perm_set
                
                avg_peer_perms = sum(peer_perm_counts) / len(peer_perm_counts)
                
                comparison_result.update({
                    "peer_avg_permissions": round(avg_peer_perms, 1),
                    "user_vs_peer_difference": len(user_perms) - avg_peer_perms,
                    "permissions_only_user_has": list(unique_to_user),
                    "common_permissions_user_missing": list(missing_from_user),
                    "peer_permission_range": f"{min(peer_perm_counts)}-{max(peer_perm_counts)}",
                })
                
                # Determine if user is an outlier
                if len(user_perms) > avg_peer_perms + 3:
                    comparison_result["outlier_status"] = "HIGH_PERMISSIONS"
                elif len(user_perms) < avg_peer_perms - 2:
                    comparison_result["outlier_status"] = "LOW_PERMISSIONS"
                else:
                    comparison_result["outlier_status"] = "NORMAL"
                    
            else:
                comparison_result.update({
                    "peer_avg_permissions": "No exact peers to compare",
                    "outlier_status": "UNIQUE_ROLE"
                })
            
            # Add some peer examples for context
            if len(exact_peers) > 0:
                peer_examples = []
                for _, peer in exact_peers.head(3).iterrows():
                    peer_perm_count = len(str(peer['permissions']).split(','))
                    peer_examples.append({
                        "username": peer['username'],
                        "permission_count": peer_perm_count
                    })
                comparison_result["peer_examples"] = peer_examples
            
            self.status = f"✅ Compared {username} with {len(exact_peers)} exact peers"
            return Data(value=comparison_result)
            
        except Exception as e:
            self.status = f"❌ Comparison failed: {str(e)}"
            return Data(value={"error": f"Peer comparison failed: {str(e)}"})