import type { LayoutServerLoad } from './$types';

import { buildChatSystemPrompt, chatTutorLabel } from '$lib/chat';
import { aiEnabled, aiModel, aiTutorName } from '$lib/config';

export const load: LayoutServerLoad = () => {
  if (!aiEnabled) {
    return { chat: null };
  }

  return {
    chat: {
      model: aiModel,
      systemPrompt: buildChatSystemPrompt(),
      tutorName: aiTutorName,
      tutorLabel: chatTutorLabel(aiTutorName),
    },
  };
};
