// Netlify Edge Function (update 54, go-live): the live site on qpall.com / www.qpall.com may be indexed; the same deploy
// on the test addresses (staging.qpall.com, *.netlify.app, deploy previews) must not. This adds
// "X-Robots-Tag: noindex, nofollow" to every response on any other host. Assets and downloads are skipped (cheaper;
// downloads already carry their own noindex). On an error the request goes through unchanged (onError: bypass).
const LIVE = new Set(['qpall.com', 'www.qpall.com']);

export default async (request, context) => {
  const res = await context.next();
  if (LIVE.has(new URL(request.url).hostname)) return res;
  const out = new Response(res.body, res);
  out.headers.set('X-Robots-Tag', 'noindex, nofollow');
  return out;
};

export const config = {
  path: '/*',
  excludedPath: ['/assets/*', '/pagefind/*', '/downloads/*'],
  onError: 'bypass',
};
