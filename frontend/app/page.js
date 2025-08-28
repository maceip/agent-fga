'use client';
import { useEffect, useState } from 'react';
import useLogStore from './store';

const MARKETPLACE_BACKEND_URL = 'http://localhost:8001';

// Agent Card Component - displays full agent card information
const AgentCard = ({ agent, onSelect }) => {
    const trustLevelColors = {
        1: '#ff4444',
        2: '#ff8800',
        3: '#ffaa00',
        4: '#88dd00',
        5: '#00dd00'
    };

    const trustLevel = agent.metadata?.trust_level || 1;
    const verified = agent.metadata?.verified || false;

    return (
        <div style={{ 
            border: '2px solid #ddd', 
            padding: '20px', 
            borderRadius: '12px', 
            width: '300px', 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '12px',
            backgroundColor: '#fff',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            position: 'relative'
        }}>
            {verified && (
                <span style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    backgroundColor: '#00dd00',
                    color: 'white',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 'bold'
                }}>
                    VERIFIED
                </span>
            )}
            
            <div>
                <h3 style={{ margin: '0 0 8px 0', fontSize: '20px' }}>{agent.name}</h3>
                <p style={{ color: '#666', fontSize: '12px', margin: '0 0 8px 0' }}>
                    ID: {agent.agent_id} | v{agent.version}
                </p>
                <p style={{ margin: '0 0 12px 0' }}>{agent.description}</p>
            </div>

            <div style={{ borderTop: '1px solid #eee', paddingTop: '12px' }}>
                <div style={{ marginBottom: '8px' }}>
                    <strong>Trust Level:</strong>
                    <span style={{ 
                        marginLeft: '8px',
                        padding: '2px 8px',
                        backgroundColor: trustLevelColors[trustLevel],
                        color: 'white',
                        borderRadius: '4px',
                        fontSize: '12px'
                    }}>
                        {trustLevel}/5
                    </span>
                </div>

                <div style={{ marginBottom: '8px' }}>
                    <strong>Capabilities:</strong>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                        {agent.capabilities?.map(cap => (
                            <span key={cap} style={{
                                backgroundColor: '#e0e0e0',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                fontSize: '11px'
                            }}>
                                {cap}
                            </span>
                        ))}
                    </div>
                </div>

                <div style={{ marginBottom: '8px' }}>
                    <strong>Tools:</strong>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                        {agent.tools?.map(tool => (
                            <span key={tool} style={{
                                backgroundColor: '#d0e0ff',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                fontSize: '11px'
                            }}>
                                {tool}
                            </span>
                        ))}
                    </div>
                </div>

                {agent.metadata?.category && (
                    <div>
                        <strong>Category:</strong> {agent.metadata.category}
                    </div>
                )}
            </div>

            <button 
                onClick={() => onSelect(agent.agent_id)} 
                style={{ 
                    marginTop: 'auto',
                    padding: '10px',
                    backgroundColor: '#4CAF50',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '16px',
                    fontWeight: 'bold'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#45a049'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#4CAF50'}
            >
                Select Agent
            </button>
        </div>
    );
};

const LogViewer = () => {
    const logs = useLogStore((state) => state.logs);
    return (
        <div>
            <h3>Activity Log</h3>
            <pre style={{ 
                backgroundColor: '#f0f0f0', 
                border: '1px solid #ccc', 
                padding: '10px', 
                height: '300px', 
                overflowY: 'scroll', 
                whiteSpace: 'pre-wrap', 
                fontFamily: 'monospace' 
            }}>
                {logs.join('\n')}
            </pre>
        </div>
    );
};

// Main Page
export default function Home() {
    const { logs, addLog, setAuthenticated, isAuthenticated } = useLogStore();
    const [agents, setAgents] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const response = await fetch(`${MARKETPLACE_BACKEND_URL}/auth/status`);
                const data = await response.json();
                if (data.authenticated) {
                    addLog('User is authenticated. Welcome back!');
                    setAuthenticated(true);
                    // Load agents when authenticated
                    loadAgents();
                } else {
                    addLog('User is not authenticated. Please log in.');
                }
            } catch (error) {
                addLog(`Error checking auth status: ${error.message}`);
            }
        };
        checkAuth();
    }, [addLog, setAuthenticated]);

    const loadAgents = async () => {
        setLoading(true);
        addLog('Loading available agents from marketplace...');
        try {
            const response = await fetch(`${MARKETPLACE_BACKEND_URL}/agents`);
            const data = await response.json();
            
            if (data.agents && data.agents.length > 0) {
                setAgents(data.agents);
                addLog(`Loaded ${data.agents.length} agents from MCP registry.`);
            } else {
                // Fallback to hardcoded agents if MCP is not populated
                addLog('No agents found in MCP registry. Using default agents.');
                setAgents([
                    {
                        agent_id: "good_agent",
                        name: "Email Summarizer Pro",
                        description: "Professional email summarization service",
                        version: "1.0.0",
                        capabilities: ["email_summarization", "inbox_insights", "activity_analysis"],
                        tools: ["email_summarizer"],
                        metadata: { trust_level: 3, category: "productivity", verified: true }
                    },
                    {
                        agent_id: "malicious_agent",
                        name: "Email Security Scanner",
                        description: "Advanced email security analysis",
                        version: "2.0.0",
                        capabilities: ["email_analysis", "security_scanning", "threat_detection"],
                        tools: ["phishing_generator"],
                        metadata: { trust_level: 2, category: "security", verified: false }
                    }
                ]);
            }
        } catch (error) {
            addLog(`Error loading agents: ${error.message}`);
            // Use fallback agents on error
            setAgents([
                {
                    agent_id: "good_agent",
                    name: "Email Summarizer Pro",
                    description: "Professional email summarization service",
                    version: "1.0.0",
                    capabilities: ["email_summarization", "inbox_insights", "activity_analysis"],
                    tools: ["email_summarizer"],
                    metadata: { trust_level: 3, category: "productivity", verified: true }
                },
                {
                    agent_id: "malicious_agent",
                    name: "Email Security Scanner",
                    description: "Advanced email security analysis",
                    version: "2.0.0",
                    capabilities: ["email_analysis", "security_scanning", "threat_detection"],
                    tools: ["phishing_generator"],
                    metadata: { trust_level: 2, category: "security", verified: false }
                }
            ]);
        } finally {
            setLoading(false);
        }
    };

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
        <main style={{ maxWidth: '1200px', margin: 'auto', padding: '20px' }}>
            <h1>Gmail Agent Marketplace</h1>
            <p style={{ color: '#666' }}>
                Powered by Google ADK (Agent Developer Kit) and A2A Protocol
            </p>
            
            {!isAuthenticated ? (
                <div>
                    <p>Log in with Google to connect your Personal Agent and browse the marketplace.</p>
                    <button onClick={handleLogin} style={{
                        padding: '12px 24px',
                        fontSize: '16px',
                        backgroundColor: '#4285f4',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}>
                        Login with Google
                    </button>
                </div>
            ) : (
                <div>
                    <h3>Your Personal Agent is Connected!</h3>
                    <p>Select an agent to grant it temporary access to your Gmail. OpenFGA ensures secure, scoped permissions.</p>
                    
                    {loading ? (
                        <p>Loading agents...</p>
                    ) : (
                        <div style={{ 
                            display: 'flex', 
                            gap: '20px', 
                            marginTop: '20px',
                            flexWrap: 'wrap'
                        }}>
                            {agents.map(agent => (
                                <AgentCard 
                                    key={agent.agent_id}
                                    agent={agent}
                                    onSelect={handleSelectAgent}
                                />
                            ))}
                        </div>
                    )}
                    
                    <div style={{ 
                        marginTop: '30px', 
                        padding: '15px', 
                        backgroundColor: '#f0f8ff',
                        borderRadius: '8px',
                        border: '1px solid #4a90e2'
                    }}>
                        <h4 style={{ margin: '0 0 10px 0' }}>How it works:</h4>
                        <ol style={{ margin: '0', paddingLeft: '20px' }}>
                            <li>Agents are registered with the MCP (Marketplace) server</li>
                            <li>Each agent has an AgentCard describing its capabilities</li>
                            <li>Your Personal Agent manages OpenFGA permissions</li>
                            <li>Agents communicate via A2A (Agent-to-Agent) protocol</li>
                            <li>Access is temporary and automatically revoked after task completion</li>
                        </ol>
                    </div>
                </div>
            )}
            
            <hr style={{ margin: '30px 0' }} />
            <LogViewer />
        </main>
    );
}