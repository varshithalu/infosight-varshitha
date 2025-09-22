import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";
// Import the "three dots" icon and the "send" icon
import { FiSend, FiMoreVertical } from "react-icons/fi";

const ChatPage = () => {
  const { logout } = useAuth();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // --- State and Ref for the dropdown menu ---
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // --- Effect to close the menu when clicking outside ---
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    };
    if (isMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isMenuOpen]);

  // Effect to fetch initial chat history
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await api.get("/chat/history");
        setMessages(response.data);
      } catch (error) {
        console.error("Failed to fetch history:", error);
      }
    };
    fetchHistory();
  }, []);

  // Effect to scroll to the bottom of the chat on new messages
  useEffect(scrollToBottom, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    const userMessage = { role: "user", content: newMessage };
    setMessages((prev) => [...prev, userMessage]);
    setNewMessage("");
    setIsLoading(true);

    try {
      const response = await api.post("/chat/chat", { content: newMessage });
      const botMessage = { role: "model", content: response.data.content };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Failed to send message:", error);
      const errorMessage = {
        role: "model",
        content: "Sorry, something went wrong.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = async () => {
    // We can close the menu before showing the confirm dialog
    setIsMenuOpen(false);
    if (window.confirm("Are you sure you want to clear the chat history?")) {
      try {
        await api.delete("/chat/history");
        setMessages([]);
      } catch (error) {
        console.error("Failed to clear history:", error);
        alert("Could not clear chat history.");
      }
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <div className="bot-info">
          <div className="status-indicator"></div>
          <h1>Chat with Ishaan!</h1>
        </div>

        <div className="header-menu-container" ref={menuRef}>
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="icon-button"
            title="Options"
          >
            <FiMoreVertical />
          </button>

          {isMenuOpen && (
            <div className="dropdown-menu">
              <button onClick={handleClearChat} className="dropdown-item">
                Clear Chat
              </button>
              <button onClick={logout} className="dropdown-item logout-option">
                Logout
              </button>
            </div>
          )}
        </div>
      </header>

      <div className="message-list">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            {msg.role === "model" && <div className="avatar">R</div>}
            <div className="message-content">
              <div className="message-bubble">
                <p>{msg.content}</p>
              </div>
              <span className="timestamp">
                {new Date().toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message model">
            <div className="avatar">R</div>
            <div className="message-content">
              <div className="message-bubble typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form className="message-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading}
          className="send-button"
          title="Send Message"
        >
          <FiSend />
        </button>
      </form>
    </div>
  );
};

export default ChatPage;
