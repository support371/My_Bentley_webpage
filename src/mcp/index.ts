/**
 * Bentley Showcase MCP Server
 * Model Context Protocol - Streamable HTTP Transport
 * Cloudflare Workers + D1
 */

type D1PreparedStatement = {
  bind: (...values: unknown[]) => D1PreparedStatement;
  first: <T = Record<string, unknown>>() => Promise<T | null>;
  all: <T = Record<string, unknown>>() => Promise<{ results: T[] }>;
};

type D1Database = {
  prepare: (query: string) => D1PreparedStatement;
};

export interface Env {
  DB: D1Database;
}

type JsonRpcId = number | string | null;

interface MCPRequest {
  jsonrpc?: string;
  method?: string;
  params?: Record<string, unknown>;
  id?: JsonRpcId;
}

const SERVER_INFO = {
  name: "bentley-showcase-mcp",
  version: "1.0.0",
};

const PROTOCOL_VERSION = "2025-03-26";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, MCP-Protocol-Version, Mcp-Session-Id",
  "Access-Control-Expose-Headers": "Mcp-Session-Id",
  "Access-Control-Max-Age": "86400",
};

function json(data: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Content-Type-Options": "nosniff",
      ...CORS_HEADERS,
      ...headers,
    },
  });
}

function mcpResponse(id: JsonRpcId | undefined, result: unknown): Response {
  return json({ jsonrpc: "2.0", id: id ?? null, result });
}

function mcpError(id: JsonRpcId | undefined, code: number, message: string): Response {
  return json({ jsonrpc: "2.0", id: id ?? null, error: { code, message } });
}

function notificationAccepted(): Response {
  return new Response(null, {
    status: 202,
    headers: CORS_HEADERS,
  });
}

async function readJsonRpcRequest(request: Request): Promise<MCPRequest | MCPRequest[] | null> {
  try {
    return await request.json();
  } catch {
    return null;
  }
}

async function selectAll(env: Env, query: string, values: unknown[] = []) {
  return env.DB.prepare(query).bind(...values).all<Record<string, unknown>>();
}

async function selectFirst(env: Env, query: string, values: unknown[] = []) {
  return env.DB.prepare(query).bind(...values).first<Record<string, unknown>>();
}

const handlers: Record<string, (params: Record<string, unknown>, env: Env) => Promise<unknown>> = {
  "initialize": async () => ({
    protocolVersion: PROTOCOL_VERSION,
    capabilities: {
      tools: { listChanged: false },
      resources: { subscribe: false, listChanged: false },
      prompts: { listChanged: false },
      logging: {},
    },
    serverInfo: SERVER_INFO,
  }),

  "ping": async () => ({}),

  "tools/list": async () => ({
    tools: [
      {
        name: "health_check",
        description: "Check Bentley Showcase backend health and D1 database connectivity.",
        inputSchema: { type: "object", properties: {}, required: [] },
      },
      {
        name: "list_projects",
        description: "List projects with optional status filter.",
        inputSchema: {
          type: "object",
          properties: {
            status: { type: "string", enum: ["active", "completed", "archived", "on_hold"] },
            limit: { type: "number", minimum: 1, maximum: 100 },
          },
          required: [],
        },
      },
      {
        name: "get_project",
        description: "Get project details by project ID.",
        inputSchema: {
          type: "object",
          properties: { project_id: { type: "string" } },
          required: ["project_id"],
        },
      },
      {
        name: "get_workspace",
        description: "Get workspace details by workspace ID.",
        inputSchema: {
          type: "object",
          properties: { workspace_id: { type: "string" } },
          required: ["workspace_id"],
        },
      },
      {
        name: "get_user",
        description: "Get user profile by user ID.",
        inputSchema: {
          type: "object",
          properties: { user_id: { type: "string" } },
          required: ["user_id"],
        },
      },
      {
        name: "get_audit_log",
        description: "Retrieve recent audit log entries.",
        inputSchema: {
          type: "object",
          properties: {
            limit: { type: "number", minimum: 1, maximum: 100 },
            action: { type: "string" },
          },
          required: [],
        },
      },
    ],
  }),

  "tools/call": async (params, env) => {
    const name = String(params.name ?? "");
    const args = (params.arguments ?? {}) as Record<string, unknown>;

    try {
      switch (name) {
        case "health_check": {
          let database = "connected";
          try {
            await env.DB.prepare("SELECT 1 AS ok").first();
          } catch (error) {
            database = "disconnected";
          }

          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  status: "healthy",
                  service: "bentley-mcp",
                  database,
                  timestamp: new Date().toISOString(),
                }),
              },
            ],
          };
        }

        case "list_projects": {
          const limit = Math.min(Math.max(Number(args.limit ?? 20), 1), 100);
          const values: unknown[] = [];
          let query = "SELECT id, name, status, created_at, updated_at FROM projects";

          if (args.status) {
            query += " WHERE status = ?";
            values.push(String(args.status));
          }

          query += " ORDER BY updated_at DESC LIMIT ?";
          values.push(limit);

          const result = await selectAll(env, query, values);
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({ projects: result.results, count: result.results.length }),
              },
            ],
          };
        }

        case "get_project": {
          const projectId = String(args.project_id ?? "");
          if (!projectId) {
            return { content: [{ type: "text", text: JSON.stringify({ error: "project_id required" }) }], isError: true };
          }

          const project = await selectFirst(env, "SELECT * FROM projects WHERE id = ?", [projectId]);
          return project
            ? { content: [{ type: "text", text: JSON.stringify(project) }] }
            : { content: [{ type: "text", text: JSON.stringify({ error: "Project not found" }) }], isError: true };
        }

        case "get_workspace": {
          const workspaceId = String(args.workspace_id ?? "");
          if (!workspaceId) {
            return { content: [{ type: "text", text: JSON.stringify({ error: "workspace_id required" }) }], isError: true };
          }

          const workspace = await selectFirst(env, "SELECT * FROM workspaces WHERE id = ?", [workspaceId]);
          return workspace
            ? { content: [{ type: "text", text: JSON.stringify(workspace) }] }
            : { content: [{ type: "text", text: JSON.stringify({ error: "Workspace not found" }) }], isError: true };
        }

        case "get_user": {
          const userId = String(args.user_id ?? "");
          if (!userId) {
            return { content: [{ type: "text", text: JSON.stringify({ error: "user_id required" }) }], isError: true };
          }

          const user = await selectFirst(
            env,
            "SELECT id, email, name, role, workspace_id, created_at FROM users WHERE id = ?",
            [userId],
          );
          return user
            ? { content: [{ type: "text", text: JSON.stringify(user) }] }
            : { content: [{ type: "text", text: JSON.stringify({ error: "User not found" }) }], isError: true };
        }

        case "get_audit_log": {
          const limit = Math.min(Math.max(Number(args.limit ?? 20), 1), 100);
          const values: unknown[] = [];
          let query = "SELECT id, user_id, action, resource_type, resource_id, details, created_at FROM audit_log";

          if (args.action) {
            query += " WHERE action = ?";
            values.push(String(args.action));
          }

          query += " ORDER BY created_at DESC LIMIT ?";
          values.push(limit);

          const result = await selectAll(env, query, values);
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({ entries: result.results, count: result.results.length }),
              },
            ],
          };
        }

        default:
          return {
            content: [{ type: "text", text: JSON.stringify({ error: `Unknown tool: ${name}` }) }],
            isError: true,
          };
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Internal error";
      return { content: [{ type: "text", text: JSON.stringify({ error: message }) }], isError: true };
    }
  },

  "resources/list": async () => ({ resources: [] }),

  "prompts/list": async () => ({ prompts: [] }),
};

async function handleMcpMessage(message: MCPRequest, env: Env): Promise<Response> {
  if (message.jsonrpc !== "2.0" || !message.method) {
    return mcpError(message.id, -32600, "Invalid Request");
  }

  if (message.method === "notifications/initialized" || typeof message.id === "undefined") {
    return notificationAccepted();
  }

  const handler = handlers[message.method];
  if (!handler) {
    return mcpError(message.id, -32601, `Method not found: ${message.method}`);
  }

  try {
    const result = await handler(message.params ?? {}, env);
    return mcpResponse(message.id, result);
  } catch {
    return mcpError(message.id, -32603, "Internal error");
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    if (url.pathname === "/health") {
      return json({ status: "healthy", service: "bentley-mcp", timestamp: new Date().toISOString() });
    }

    if (url.pathname === "/") {
      return json({
        service: SERVER_INFO.name,
        version: SERVER_INFO.version,
        protocol: "MCP",
        protocolVersion: PROTOCOL_VERSION,
        transport: "streamable-http",
        endpoints: { mcp: "/mcp", health: "/health" },
      });
    }

    if (url.pathname !== "/mcp") {
      return json({ error: "Not found" }, 404);
    }

    if (request.method !== "POST") {
      return json({ error: "Method not allowed. Use POST for MCP." }, 405);
    }

    const body = await readJsonRpcRequest(request);
    if (!body) {
      return mcpError(null, -32700, "Parse error");
    }

    if (Array.isArray(body)) {
      const responses: unknown[] = [];
      for (const message of body) {
        const response = await handleMcpMessage(message, env);
        if (response.status !== 202) {
          responses.push(await response.json());
        }
      }
      return json(responses);
    }

    return handleMcpMessage(body, env);
  },
};
