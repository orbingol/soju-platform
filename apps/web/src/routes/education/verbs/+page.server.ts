import { redirect } from '@sveltejs/kit';
import { base } from '$app/paths';

export const prerender = true;

export const load = () => {
  redirect(301, `${base}/education/words/verbs/`);
};
