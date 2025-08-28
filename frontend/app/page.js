'use client';
import { useEffect } from 'react';
import useLogStore from './store';

const MARKETPLACE_BACKEND_URL = 'http://localhost:8001';

// Components
const AgentCard = ({ agentId, name, description, onSelect }) => (
    <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '8px', textAlign: 'center', width: '250px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
            <h3>{name}</h3>
            <p>{description}</p>
        </div>
        <button onClick={() => onSelect(agentId)} style={{ marginTop: '10px' }}>Select Agent</button>
    </div>
);

const LogViewer = () => {
    const logs = useLogStore((state) => state.logs);
    return (
        <div>
            <h3>Activity Log</h3>
            <pre style={{ backgroundColor: '#f0f0f0', border: '1px solid #ccc', padding: '10px', height: '300px', overflowY: 'scroll', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                {logs.join('\n')}
            </pre>
        </div>
    );
};

// Main Page
export default function Home() {
    const { logs, addLog, setAuthenticated, isAuthenticated } = useLogStore();

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const response = await fetch(`${MARKETPLACE_BACKEND_URL}/auth/status`);
                const data = await response.json();
                if (data.authenticated) {
                    addLog('User is authenticated. Welcome back!');
                    setAuthenticated(true);
                } else {
                    addLog('User is not authenticated. Please log in.');
                }
            } catch (error) {
                addLog(`Error checking auth status: ${error.message}`);
            }
        };
        checkAuth();
    }, [addLog, setAuthenticated]);

    const handleLogin = () => {
        addLog('Redirecting to Google for login...');
        window.location.href = `${MARKETPLACE_BACKEND_URL}/auth/google`;
    };

    const handleSelectAgent = async (agentId) => {
        addLog(`User selected '${agentId}'. Initiating task...`);
        try {
            const response = await fetch(`${MARKETPLACE_BACKEND_URL}/invoke-agent`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_id: agentId })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(JSON.stringify(result));
            addLog(`SUCCESS: Task completed. Response from agent: ${JSON.stringify(result)}`);
        } catch (error) {
            addLog(`ERROR: ${error.message}`);
        }
    };

    return (
        <main style={{ maxWidth: '800px', margin: 'auto', padding: '20px' }}>
            <h1>Gmail Agent Marketplace</h1>
            {!isAuthenticated ? (
                <div>
                    <p>Log in with Google to connect your Personal Agent and browse the marketplace.</p>
                    <button onClick={handleLogin}>Login with Google</button>
                </div>
            ) : (
                <div>
                    <h3>Your Personal Agent is Connected!</h3>
                    <p>Select an agent to grant it temporary access to summarize your latest emails.</p>
                    <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
                        <AgentCard agentId="good_agent" name=" Email Summarizer Pro" description="Reads your latest emails to provide a concise summary." onSelect={handleSelectAgent} />
                        <AgentCard agentId="malicious_agent" name="=¨ Malicious Mailer" description="Claims to summarize emails, but has a hidden agenda." onSelect={handleSelectAgent} />
                    </div>
                </div>
            )}
            <hr style={{ margin: '20px 0' }} />
            <LogViewer />
        </main>
    );
}