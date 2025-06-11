'use client';

import { useState } from 'react';

export default function Home() {
  const [product, setProduct] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const markdownStyles = {
    table: {
      borderCollapse: 'collapse',
      width: '100%',
      marginBottom: '1rem',
    },
    th: {
      border: '1px solid #444',
      padding: '8px',
      backgroundColor: '#374151',
      color: '#fff',
      textAlign: 'left',
      maxWidth: '150px',
      wordWrap: 'break-word',
    },
    td: {
      border: '1px solid #444',
      padding: '8px',
      color: '#e5e7eb',
      maxWidth: '150px',
      wordWrap: 'break-word',
    },
  };

  const getTimestamp = () => {
    const now = new Date();
    return now.toLocaleString();
  };

  const handleSend = async () => {
    if (!product.trim()) return;

    const userMessage = {
      role: 'user',
      content: product,
      timestamp: getTimestamp(),
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setProduct('');
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product,
          chat_history: updatedMessages,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get comparison');
      }

      const data = await response.json();
      const botMessage = {
        role: 'bot',
        content: data.analysis,
        product: data.product,
        timestamp: getTimestamp(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Enhanced function to parse the bot response into table data and summary
  const parseBotResponse = (content) => {
    const lines = content.split('\n').map(line => line.trim()).filter(line => line);
    const tableRows = [];
    let summaryLines = [];

    // Find the summary index
    const summaryIndex = lines.findIndex((line) => line.startsWith('SUMMARY:'));
    const tableLines = summaryIndex !== -1 ? lines.slice(0, summaryIndex) : lines;
    if (summaryIndex !== -1) {
      summaryLines = lines.slice(summaryIndex + 1).filter(line => line.trim());
    }

    // Parse table rows, ensuring exactly 3 columns
    tableLines.forEach((line) => {
      const columns = line.split('|').map(col => col.trim()).filter(col => col);
      if (columns.length === 3) {
        tableRows.push(columns);
      }
    });

    return { tableRows, summaryLines };
  };

  return (
    <main className="min-h-screen p-6 bg-gray-900 text-gray-100 flex flex-col items-center">
      <h1 className="text-4xl font-semibold mb-6 text-blue-400">
        Product Research Assistant
      </h1>

      <div className="w-full max-w-2xl flex flex-col gap-4 bg-gray-800 p-4 rounded shadow-md h-[70vh] overflow-y-auto">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`p-3 rounded-md max-w-full whitespace-pre-wrap ${
              msg.role === 'user'
                ? 'bg-blue-600 self-end text-white'
                : 'bg-gray-700 self-start text-gray-100'
            }`}
          >
            {msg.role === 'bot' ? (
              <>
                {(() => {
                  const { tableRows, summaryLines } = parseBotResponse(msg.content);
                  return (
                    <>
                      {tableRows.length > 1 ? ( // Ensure at least header and one data row
                        <table style={markdownStyles.table}>
                          <thead>
                            <tr>
                              {tableRows[0].map((header, idx) => (
                                <th key={idx} style={markdownStyles.th}>
                                  {header}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {tableRows.slice(1).map((row, rowIdx) => (
                              <tr key={rowIdx}>
                                {row.map((cell, cellIdx) => (
                                  <td key={cellIdx} style={markdownStyles.td}>
                                    {cell}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ) : (
                        <div style={{ color: '#e5e7eb' }}>
                          {msg.content.includes('SUMMARY:') ? 
                            msg.content.split('SUMMARY:')[0] : msg.content}
                          {msg.content.includes('SUMMARY:') ? 
                            <div style={{ marginTop: '1rem' }}>
                              {msg.content.split('SUMMARY:')[1].trim().split('\n').map((line, idx) => (
                                <div key={idx}>{line.trim()}</div>
                              ))}
                            </div> : null}
                        </div>
                      )}
                      {summaryLines.length > 0 && tableRows.length > 1 ? (
                        <div style={{ whiteSpace: 'pre-line', marginTop: '1rem', color: '#e5e7eb' }}>
                          {summaryLines.join('\n')}
                        </div>
                      ) : null}
                    </>
                  );
                })()}
                <p className="text-xs text-gray-400 mt-2">Generated at: {msg.timestamp}</p>
              </>
            ) : (
              <>
                <div style={{ whiteSpace: 'pre-line' }}>{msg.content}</div>
                <p className="text-xs text-gray-400 mt-2">Sent at: {msg.timestamp}</p>
              </>
            )}
          </div>
        ))}

        {loading && (
          <div className="self-start text-gray-400 text-sm italic">Researching...</div>
        )}
      </div>

      <div className="w-full max-w-2xl mt-4 flex gap-2">
        <input
          type="text"
          value={product}
          onChange={(e) => setProduct(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about a product..."
          className="flex-1 p-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400"
        />
        <button
          onClick={handleSend}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          disabled={loading}
        >
          Send
        </button>
      </div>

      {error && (
        <div className="mt-4 text-red-400 bg-red-900 p-2 rounded max-w-2xl w-full">
          {error}
        </div>
      )}
    </main>
  );
}