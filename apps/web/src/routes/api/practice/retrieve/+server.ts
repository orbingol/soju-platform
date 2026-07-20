import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

import { getDataDir } from '$lib/data/paths';
import { PracticeRetrieveError, retrievePractice } from '$lib/practice/retrieve';
import { devLocalOnlyGuard } from '$lib/server/dev-only';

export const prerender = false;

interface RetrieveRequestBody {
  level?: string;
  queryVector?: unknown;
  vocabK?: number;
  grammarM?: number;
}

export const POST: RequestHandler = async ({ request, getClientAddress }) => {
  const guardResponse = devLocalOnlyGuard(request, getClientAddress, 'Practice retrieve API');
  if (guardResponse) return guardResponse;

  let body: RetrieveRequestBody;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  if (!Array.isArray(body.queryVector)) {
    return json({ error: 'queryVector must be an array of numbers' }, { status: 400 });
  }

  try {
    const result = retrievePractice(
      {
        level: body.level,
        queryVector: body.queryVector as number[],
        vocabK: body.vocabK,
        grammarM: body.grammarM
      },
      getDataDir()
    );
    return json(result);
  } catch (err) {
    if (err instanceof PracticeRetrieveError) {
      return json({ error: err.message }, { status: err.status });
    }
    return json({ error: err instanceof Error ? err.message : 'Retrieve failed' }, { status: 500 });
  }
};
