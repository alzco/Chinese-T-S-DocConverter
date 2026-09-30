import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "apikey, content-type",
};

function respond(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

function validMapping(value: unknown): value is Record<string, string> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const entries = Object.entries(value);
  return entries.length >= 1 && entries.length <= 500 && entries.every(
    ([source, target]) => source.trim().length >= 1 && source.length <= 64 &&
      typeof target === "string" && target.trim().length >= 1 && target.length <= 256,
  );
}

Deno.serve(async (request) => {
  if (request.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (request.method !== "POST") return respond({ error: "Method not allowed" }, 405);

  try {
    const body = await request.json();
    if (!validMapping(body.mapping)) return respond({ error: "Invalid mapping" }, 400);
    const encoded = new TextEncoder().encode(JSON.stringify(body.mapping));
    if (encoded.byteLength > 262144) return respond({ error: "Mapping too large" }, 400);

    const client = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
      { auth: { persistSession: false } },
    );

    if (body.action === "publish") {
      if (!/^[a-f0-9]{64}$/.test(body.id) || typeof body.name !== "string" ||
          body.name.trim().length < 1 || body.name.trim().length > 60) {
        return respond({ error: "Invalid dictionary" }, 400);
      }
      const { data, error } = await client.from("public_dictionaries")
        .insert({ id: body.id, name: body.name.trim(), mapping: body.mapping })
        .select("id");
      if (error?.code === "23505") return respond({ created: false });
      if (error) throw error;
      return respond({ created: Boolean(data?.length) });
    }

    if (body.action === "merge" && typeof body.target_id === "string") {
      const { data, error } = await client.rpc("merge_public_dictionary", {
        target_id: body.target_id,
        additions: body.mapping,
      });
      if (error) throw error;
      return respond({ updated: Boolean(data?.length) });
    }
    return respond({ error: "Invalid action" }, 400);
  } catch (_error) {
    return respond({ error: "Unable to update dictionary" }, 500);
  }
});
