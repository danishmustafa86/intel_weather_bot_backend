# Prompt for Lovable: Building a Modern, Production-Ready Frontend for Weather & Search AI Agent

Copy and paste the entire prompt below directly into **Lovable** to generate the complete frontend application.

---

```markdown
# Comprehensive Prompt: Build a Production-Grade AI Agent Web Application (NextJS + Vite + Tailwind CSS + Lucide + Shadcn UI)

## 1. Project Overview & Vision
Build an ultra-modern, high-performance, polished, and responsive ChatGPT-style web application for an intelligent **Weather & Search AI Agent**.
The agent is backed by a FastAPI + LangGraph system integrated with OpenWeather, Tavily Web Search, Guardrails (anti-prompt injection & safety filters), and multi-LLM fallback (Gemini, Groq, xAI) with persistent chat history in MongoDB.

The application must feel as slick, intuitive, and feature-complete as ChatGPT, Perplexity, or Claude, featuring dark/light theme switching, animated UI transitions, conversational state management, and real-time backend API connectivity.

---

## 2. Backend Architecture & API Specifications

The backend is built with FastAPI and runs locally at `http://localhost:8000`.
All API routes are prefixed with `/api`. CORS is enabled for frontend dev servers (`http://localhost:5173`, `http://localhost:3000`).

### 2.1 Backend Health & Diagnostics Endpoint
- **URL**: `GET /api/health`
- **Purpose**: Displays system status and active services in a settings or status badge.
- **Response Format (`200 OK`)**:
  ```json
  {
    "status": "ok",
    "llm_providers": ["gemini", "groq", "xai"],
    "openweather_configured": true,
    "tavily_configured": true
  }
  ```

---

### 2.2 Chat & Session Management Endpoints

#### A. List All Conversations
- **URL**: `GET /api/chats?skip=0&limit=50`
- **Purpose**: Populates the conversation sidebar with active chat threads, ordered by most recently updated.
- **Query Params**:
  - `skip` (int, default `0`)
  - `limit` (int, default `50`)
- **Response Format (`200 OK`)**: Array of `ChatSummary`
  ```json
  [
    {
      "id": "660c1d2e...",
      "title": "Weather in Tokyo & Cherry Blossom Updates",
      "created_at": "2026-10-04T12:00:00Z",
      "updated_at": "2026-10-04T12:05:00Z",
      "message_count": 4
    }
  ]
  ```

#### B. Create New Conversation
- **URL**: `POST /api/chats`
- **Header**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "title": "Optional Custom Title",
    "message": "Optional first message - if provided, the agent answers immediately"
  }
  ```
- **Response Format (`201 Created`)**: Returns full `Chat` object with messages.

#### C. Get Conversation by ID
- **URL**: `GET /api/chats/{chat_id}`
- **Purpose**: Fetches the full chat history when user selects a conversation from the sidebar.
- **Response Format (`200 OK`)**: Full `Chat` object
  ```json
  {
    "id": "660c1d2e...",
    "title": "Weather in Tokyo",
    "created_at": "2026-10-04T12:00:00Z",
    "updated_at": "2026-10-04T12:05:00Z",
    "messages": [
      {
        "id": "c1f7a0b2-3c8e-4a6f-b258-208b02e604f1",
        "role": "user",
        "content": "What is the weather in Tokyo right now?",
        "created_at": "2026-10-04T12:00:00Z"
      },
      {
        "id": "d981e6a1-9a72-4fd3-982c-473d05e219ba",
        "role": "assistant",
        "content": "Current weather in Tokyo, JP:\n- Conditions: clear sky\n- Temperature: 18°C (feels like 17°C)\n- Min/Max: 16°C / 20°C\n- Humidity: 55%\n- Wind: 3.5 m/s",
        "created_at": "2026-10-04T12:00:05Z"
      }
    ]
  }
  ```

#### D. Rename Conversation
- **URL**: `PATCH /api/chats/{chat_id}`
- **Request Body**:
  ```json
  {
    "title": "Updated Chat Title"
  }
  ```
- **Response Format (`200 OK`)**: Updated `Chat` object.

#### E. Delete Single Conversation
- **URL**: `DELETE /api/chats/{chat_id}`
- **Response Format (`200 OK`)**:
  ```json
  {
    "deleted": 1
  }
  ```

#### F. Delete All Conversations
- **URL**: `DELETE /api/chats`
- **Response Format (`200 OK`)**:
  ```json
  {
    "deleted": 12
  }
  ```

---

### 2.3 Messaging & Interaction Endpoints

#### A. Send Message in Existing Chat
- **URL**: `POST /api/chats/{chat_id}/messages`
- **Request Body**:
  ```json
  {
    "message": "What about the 5-day forecast or recent news?"
  }
  ```
- **Response Format (`200 OK`)**:
  ```json
  {
    "chat_id": "660c1d2e...",
    "user_message": {
      "id": "uuid-here",
      "role": "user",
      "content": "What about the 5-day forecast or recent news?",
      "created_at": "2026-10-04T12:06:00Z"
    },
    "assistant_message": {
      "id": "uuid-here",
      "role": "assistant",
      "content": "Here is what I found...",
      "created_at": "2026-10-04T12:06:04Z"
    }
  }
  ```

#### B. Edit Message (Branch / Rewind)
- **URL**: `PUT /api/chats/{chat_id}/messages/{message_id}`
- **Purpose**: Edits a user prompt. Like ChatGPT, all subsequent messages after this message are removed and replaced with the updated agent response.
- **Request Body**:
  ```json
  {
    "message": "Updated user question"
  }
  ```
- **Response Format (`200 OK`)**: Full updated `Chat` object.

#### C. Regenerate Last Assistant Response
- **URL**: `POST /api/chats/{chat_id}/regenerate`
- **Purpose**: Regenerates the assistant's answer for the latest question in the chat.
- **Response Format (`200 OK`)**: Full updated `Chat` object.

#### D. Delete Specific Message
- **URL**: `DELETE /api/chats/{chat_id}/messages/{message_id}`
- **Response Format (`200 OK`)**:
  ```json
  {
    "deleted": 1
  }
  ```

---

## 3. Design Aesthetics & Visual Identity

1. **Aesthetic Direction**:
   - Modern, sleek AI workspace (inspired by OpenAI ChatGPT, Vercel, Linear, and Perplexity).
   - Glassmorphic accents, soft drop shadows (`shadow-sm`, `shadow-xl`), hairline borders (`border-border/40`), and backdrop blurs (`backdrop-blur-md`).
   - Dark mode as first-class citizen with deep slate/zinc backgrounds (`#09090b`, `#18181b`), and clean crisp high-contrast light mode.
2. **Typography**:
   - Sans-serif font hierarchy (Inter, Plus Jakarta Sans, or Geist) with clear readability for code snippets, bullet points, and meteorological weather data.
3. **Rich Message Content Formatting**:
   - **Markdown Rendering**: Support standard Markdown, GFM tables, clickable links, lists, blockquotes, and code blocks with syntax highlighting and a "Copy Code" button.
   - **Weather Card Widgets**: When agent output contains weather metrics (e.g., `Conditions`, `Temperature`, `Humidity`, `Wind`), render an elegant, specialized **Weather Card Widget** with weather icons (sun, cloud-rain, wind, thermometer) alongside the raw text.
   - **Web Search Citation Badges**: When web search results contain `[1]`, `URL:`, or source references, render them as clean clickable pill badges/cards showing domain and link preview.
4. **Micro-interactions & UX Delight**:
   - Smooth sidebar toggle (collapsible for mobile & clean desktop workspace).
   - Shimmer/skeleton pulse loader or bouncing typing indicator while the assistant generates an answer.
   - Auto-scrolling to bottom on new messages with an intuitive "Scroll to bottom" button when user scrolls up.
   - Toast notifications for error handling (e.g., 502 AI Agent error, network failure, chat deletion).
   - Confirmation dialog modals for destructive actions ("Delete chat", "Clear all chats").

---

## 4. Frontend Component Hierarchy & Recommended Folder Structure

Create a clean, scalable folder architecture following modern React best practices:

```
frontend/
├── public/
│   └── favicon.svg
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatContainer.tsx         # Main chat scroll area & welcome screen
│   │   │   ├── ChatHeader.tsx            # Header with title, rename inline, status badge, model info
│   │   │   ├── ChatInput.tsx             # Textarea with auto-resize, send on Enter, keyboard shortcuts
│   │   │   ├── MessageList.tsx           # Virtualized or mapped list of messages
│   │   │   ├── MessageItem.tsx           # Single message bubble (user vs assistant)
│   │   │   ├── MessageActions.tsx        # Copy, Edit prompt, Regenerate, Delete message
│   │   │   ├── WeatherCard.tsx           # Detected weather data visual card
│   │   │   ├── SearchSources.tsx         # Tavily citation badges / external links
│   │   │   └── TypingIndicator.tsx       # Animated thinking state
│   │   ├── sidebar/
│   │   │   ├── Sidebar.tsx               # Collapsible sidebar wrapper
│   │   │   ├── ChatList.tsx              # List of recent chats grouped by date (Today, Yesterday, 7 Days)
│   │   │   ├── ChatListItem.tsx          # Chat thread item with edit/delete dropmenu
│   │   │   ├── NewChatButton.tsx         # "+ New Chat" CTA button
│   │   │   └── SystemStatus.tsx          # Small footer widget showing API & provider health
│   │   ├── common/
│   │   │   ├── ConfirmModal.tsx          # Dialog for confirming delete
│   │   │   ├── ThemeToggle.tsx           # Dark / Light theme switcher
│   │   │   └── EmptyState.tsx            # Suggested prompt starters (e.g. "What's the weather in Paris?", "Search AI news")
│   │   └── ui/                           # Shadcn UI primitives (Button, Dialog, Dropdown, Input, Toast, Tooltip)
│   ├── hooks/
│   │   ├── useChats.ts                   # SWR or React Query hook for managing chat threads
│   │   ├── useActiveChat.ts             # Hook for active conversation, sending & regenerating messages
│   │   └── useHealth.ts                  # Polling/fetching /api/health
│   ├── services/
│   │   └── api.ts                        # Axios or Fetch client with baseUrl & error handling
│   ├── types/
│   │   └── index.ts                      # TypeScript interfaces matching backend models exactly
│   ├── utils/
│   │   ├── formatters.ts                 # Date/time formatting, text parsers
│   │   └── weatherParser.ts             # Regex/parser for extracting weather properties
│   ├── App.tsx                           # Master layout combining Sidebar + ChatView
│   ├── main.tsx
│   └── index.css                         # Tailwind CSS directives & theme variables
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

---

## 5. TypeScript Data Contracts (Must match backend schemas)

```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface Chat {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ChatSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatReply {
  chat_id: string;
  user_message: Message;
  assistant_message: Message;
}

export interface DeleteResponse {
  deleted: number;
}

export interface HealthResponse {
  status: string;
  llm_providers: string[];
  openweather_configured: boolean;
  tavily_configured: boolean;
}
```

---

## 6. Functional Requirements & User Flows

1. **New Conversation**:
   - Clicking "New Chat" clears the active chat view and displays the **EmptyState** screen with quick prompts (e.g., *"What is the weather in New York?"*, *"Search latest tech news about quantum computing"*, *"Check weather in Tokyo and tell me popular spots to visit"*).
   - Typing in the input creates a new chat automatically using `POST /api/chats` and redirects the active URL/state to the new `chat_id`.
2. **Follow-up Interaction**:
   - Submitting prompts in an existing chat calls `POST /api/chats/{chat_id}/messages`.
   - Assistant response is displayed with full formatting.
3. **Editing Messages**:
   - Hovering a user message shows an "Edit" button. Clicking it turns the message into an inline editable textarea.
   - Saving calls `PUT /api/chats/{chat_id}/messages/{message_id}`, truncating the future conversation and streaming/rendering the updated reply.
4. **Regenerate Answer**:
   - On the latest assistant message, provide a "Regenerate" button calling `POST /api/chats/{chat_id}/regenerate`.
5. **Rename & Delete**:
   - Chat title in the header and sidebar items can be renamed with inline editing or a prompt dialog.
   - Deletion removes the thread smoothly with an optimistic UI update.
6. **Guardrail & Error Notification**:
   - If user triggers guardrails (empty, >4000 characters, injection prompt), display friendly error toast or message.
   - If backend returns `502 Bad Gateway`, show an alert badge explaining that AI models or keys encountered an error.

---

## 7. Deliverable Goal
Generate the full, executable React + Vite + TypeScript application code with beautiful styling, complete API client, and seamless user experience. Ensure all API calls point to `VITE_API_BASE_URL` (defaulting to `http://localhost:8000/api`).
```
