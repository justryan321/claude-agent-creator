// End-to-end test of the Interactive Builder: a real server and a real page in Chromium,
// with Claude's side simulated through builder_server.py's command line.
//
//   node tests/interactive-builder.e2e.js        (needs Node, Python 3, and Playwright with Chromium)
//
// Screenshots and the transcript are written to a temporary folder printed at the end.
const { chromium } = require('playwright');
const os = require('os');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const SKILL = ROOT + '/plugins/agent-builder/skills/create-agent';
const SRV = SKILL + '/scripts/builder_server.py';
const EX = ROOT + '/examples/page-summarizer';
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'builder-e2e-'));
const OUT = TMP + '/out';
const HOME = TMP + '/home';
fs.rmSync(HOME, { recursive: true, force: true }); fs.mkdirSync(OUT, { recursive: true });

const cli = (...a) => execFileSync('python3', [SRV, '--home', HOME, ...a], { encoding: 'utf8' });
const send = msgs => cli('send', '--json', JSON.stringify(msgs));
const wait = (t = 10) => JSON.parse(cli('wait', '--timeout', String(t)));
let failures = 0;
function check(cond, label) { console.log((cond ? 'PASS ' : 'FAIL ') + label); if (!cond) failures++; }
async function expectEvent(type, pred = () => true) {
  const r = wait(10);
  const ev = (r.events || []).find(e => e.type === type);
  check(ev && pred(ev), `event ${type}: ${JSON.stringify(r.events)}`);
  return ev;
}

// Fake speech recognition, so voice input can be tested without a microphone.
const FAKE_SR = `
  window.SpeechRecognition = class {
    start() { this._t = setTimeout(() => {
      const mk = (t, f) => { const r = [{ transcript: t }]; r.isFinal = f; return r; };
      this.onresult && this.onresult({ results: [mk('a recipe helper', false)] });
      setTimeout(() => this.onresult && this.onresult({ results: [mk('a recipe helper for my family', true)] }), 60);
    }, 50); }
    stop() { clearTimeout(this._t); setTimeout(() => this.onend && this.onend(), 120); }
  };
  navigator.mediaDevices.getUserMedia = () => Promise.reject(new Error('no mic in test'));
`;

(async () => {
  const start = JSON.parse(cli('start'));
  const url = start.url;
  send([{ type: 'phase', step: 1, label: 'Start' },
        { type: 'say', text: "Hi! Let's build your agent together. It takes about **5–10 minutes**, and nothing is final." },
        { type: 'ask', id: 'start', text: 'How would you like to start?', style: 'cards', allow_dont_know: false, options: [
          { emoji: '📎', label: 'I already have something', description: 'A past chat, documents, notes, or old instructions.' },
          { emoji: '📋', label: 'Start from a template', description: 'Pick a ready-made agent and adjust it.' },
          { emoji: '💬', label: 'Describe it in a sentence', description: "Tell me what it should do.", recommended: true },
          { emoji: '⚡', label: 'Express: just build it', description: 'One sentence, and I fill in the rest.' }] }]);

  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 820 } });
  await ctx.addInitScript(FAKE_SR);
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(url);
  await page.waitForSelector('text=How would you like to start?');
  check(await page.locator('#steps li.now').innerText() === 'Start', 'progress shows Start');
  check(JSON.parse(cli('status')).page_open === true, 'status sees the page as open');
  await page.screenshot({ path: OUT + '/1-start.png' });

  // 1. option card → answer
  await page.click('text=Describe it in a sentence');
  await expectEvent('answer', e => e.id === 'start' && e.via === 'chip' && e.choices[0] === 'Describe it in a sentence');
  check(await page.locator('#thinking.show').count() === 1, 'thinking indicator after answering');

  // 2. free text + card updates
  send([{ type: 'phase', step: 2, label: 'Design' }, { type: 'ask', id: 'purpose', text: 'What do you want your agent to do, and for whom?' }]);
  await page.waitForSelector('text=What do you want your agent to do');
  check(await page.locator('#thinking.show').count() === 0, 'thinking hidden when question arrives');
  check(await page.locator('.b-ask.past').count() === 1, 'previous question dimmed');
  // voice: hold Space with the fake recognizer
  await page.locator('body').click({ position: { x: 5, y: 400 } });
  await page.keyboard.down('Space'); await page.waitForTimeout(300); await page.keyboard.up('Space'); await page.waitForTimeout(300);
  check((await page.inputValue('#input')) === 'a recipe helper for my family', 'push-to-talk fills the box: ' + await page.inputValue('#input'));
  await page.keyboard.press('Enter');
  await expectEvent('answer', e => e.id === 'purpose' && e.via === 'voice' && e.text === 'a recipe helper for my family');

  send([{ type: 'card', emoji: '🍲', fields: { job: { value: 'Suggests family recipes' }, for: { value: 'My family', guess: true }, asks_first: { value: 'Nothing yet', needs_answer: true } } },
        { type: 'ask', id: 'abilities', text: 'What should it be able to do?', multi: true, options: ['Search the web', 'Read files I give it', 'Just chat'] }]);
  await page.waitForSelector('text=What should it be able to do?');
  check((await page.locator('#acard').innerText()).includes('Suggests family recipes'), 'card panel shows the job');
  check(await page.locator('#acard .needs').count() === 1, 'needs-your-answer marker shown');
  check(await page.locator('#acard .guess').count() === 1, 'guess marker shown');
  await page.locator('#input').blur(); await page.keyboard.press('1'); // number shortcut toggles first chip in multi mode
  await page.click('.chip:has-text("Read files")');
  await page.click('.askfoot button.primary');
  await expectEvent('answer', e => e.choices.length === 2 && e.choices.includes('Search the web'));

  // 3. "you decide" typed command
  send([{ type: 'ask', id: 'tone', text: 'How should it sound?', options: [{ label: 'Friendly', recommended: true }, 'Short'] }]);
  await page.waitForSelector('text=How should it sound?');
  await page.fill('#input', 'you decide'); await page.keyboard.press('Enter');
  await expectEvent('answer', e => e.dont_know === true && e.id === 'tone');

  // 4. edit an earlier answer
  await page.locator('.b-user .edit').first().click();
  await page.locator('.b-user .editbox textarea').fill('Describe it, please');
  await page.click('.b-user .editbox button:has-text("Save")');
  await expectEvent('edit_answer', e => e.text === 'Describe it, please' && e.id === 'start');

  // 5. edit a card line
  await page.locator('#acard .field').first().hover();
  await page.locator('#acard .field .fe').first().click();
  await page.locator('#acard .editbox textarea').fill('Suggests quick weeknight family recipes');
  await page.keyboard.press('Enter');
  await expectEvent('edit_card', e => e.field === 'job');
  check((await page.locator('#acard').innerText()).includes('quick weeknight'), 'card edit shown');

  // 6. review card
  send([{ type: 'phase', step: 3, label: 'Card & Flow' }, { type: 'card', name: 'Recipe Pal', id: 'recipe-pal' },
        { type: 'review_card', text: "Here's your agent. Does this look right?" }]);
  await page.waitForSelector('text=Does this look right?');
  await page.waitForTimeout(700); await page.screenshot({ path: OUT + '/2-review-card.png' });
  await page.click('.b-prompt:not(.answered) button:has-text("Looks good")');
  await expectEvent('approve', e => e.what === 'card');

  // 7. flow preview from the real renderer
  execFileSync('python3', [SKILL + '/scripts/render_flow.py', EX + '/flow.json', OUT + '/flow.html']);
  send([{ type: 'flow', html_path: OUT + '/flow.html' }]);
  await page.waitForSelector('iframe.frame');
  await page.waitForTimeout(600);
  const fh = await page.locator('iframe.frame').evaluate(f => f.getBoundingClientRect().height);
  check(fh > 600, 'flow iframe sized to content: ' + fh);
  await page.screenshot({ path: OUT + '/3-flow.png' });
  await page.click('.b-prompt:not(.answered) button:has-text("Change something")');
  check(await page.locator('#modechip.show').count() === 1, 'change mode chip shown');
  await page.fill('#input', 'Add a step that checks for allergies'); await page.keyboard.press('Enter');
  await expectEvent('change', e => e.what === 'flow');

  // 8. test drive
  send([{ type: 'phase', step: 4, label: 'Test drive' }, { type: 'test_drive', name: 'Recipe Pal', emoji: '🍲' }]);
  await page.waitForSelector('#testbar.show');
  await page.fill('#input', "What's quick with chicken?"); await page.keyboard.press('Enter');
  await expectEvent('test_message', e => e.text.includes('chicken'));
  check((await page.locator('#thinkingText').innerText()).includes('Recipe Pal'), 'agent replying indicator');
  send([{ type: 'agent', text: 'Try a **15-minute lemon chicken**:\n- Chicken thighs\n- Lemon\n- Garlic' }]);
  await page.waitForSelector('.b-agent');
  await page.fill('#input', 'feedback: make it shorter'); await page.keyboard.press('Enter');
  await expectEvent('feedback', e => e.text === 'make it shorter');
  send([{ type: 'say', text: "I'll make replies shorter." }]);
  await page.waitForSelector('.b-say.note');
  await page.click('#tdFeedback'); await page.fill('#input', 'no emoji'); await page.keyboard.press('Enter');
  await expectEvent('feedback', e => e.text === 'no emoji');
  await page.waitForTimeout(700); await page.screenshot({ path: OUT + '/4-test-drive.png' });
  await page.click('#tdDone');
  await expectEvent('test_done');
  send([{ type: 'test_drive_end', text: 'Test drive finished.' }]);
  await page.waitForSelector('#testbar:not(.show)', { state: 'attached' });

  // 9. collect files
  fs.writeFileSync(OUT + '/faq.md', '# FAQ\nWe deliver on Fridays.');
  send([{ type: 'collect', id: 'ctx', text: 'Share what you already have' }]);
  await page.waitForSelector('.drop');
  await page.setInputFiles('.drop input[type=file]', OUT + '/faq.md');
  await page.waitForSelector('.filechip:has-text("faq.md")');
  await page.waitForFunction(() => !document.querySelector('.filelist').innerText.includes('uploading'));
  await page.fill('.paste', 'Old instructions: be nice.');
  await page.click('button:has-text("Share these")');
  const col = await expectEvent('collected', e => e.files.length === 1 && e.text.includes('be nice'));
  check(col && fs.readFileSync(col.files[0].path, 'utf8').includes('Fridays'), 'uploaded file saved in session folder');

  // 10. extracted
  send([{ type: 'extracted', id: 'x', text: "Here's what I picked up", items: [{ id: 'a', text: 'Delivers Fridays', source: 'faq.md' }, { id: 'b', text: 'Tone: nice', source: 'pasted text', guess: true }], gaps: ['Who uses it'] }]);
  await page.waitForSelector('.xitems');
  await page.locator('.xitems li').nth(1).locator('button:has-text("Drop")').click();
  await page.click('button:has-text("Looks right")');
  await expectEvent('extracted', e => e.accepted.join() === 'a' && e.rejected.join() === 'b');

  // 11. workflow stages + rules
  send([{ type: 'stages', stages: [{ title: 'Intake', emoji: '📞', status: 'done' }, { title: 'Estimate', emoji: '🧮', status: 'active' }, { title: 'Bid', emoji: '📄' }] },
        { type: 'rule', stage: 'Estimate', when: 'job is over $50k', do: 'add 10% contingency', why: 'surprises behind walls' },
        { type: 'rule', stage: 2, when: 'permit needed', do: 'flag it', needs_answer: true }]);
  await page.waitForSelector('#stagemap.show');
  check(await page.locator('#pbstages li').count() === 2, 'playbook shows 2 rules');
  check(await page.locator('#pbstages .pbstage').count() === 1, 'both rules grouped under Estimate');

  // 12. build progress, how to use, tests, report, user test form
  send([{ type: 'phase', step: 5, label: 'Build' }, { type: 'progress', id: 'build', items: [{ label: 'Writing instructions', status: 'done' }, { label: 'Installing', status: 'active' }] }]);
  await page.waitForSelector('.checklist');
  send([{ type: 'progress', id: 'build', items: [{ label: 'Writing instructions', status: 'done' }, { label: 'Installing', status: 'done' }] },
        { type: 'how_to_use', where: 'In Claude Code, in any project.', first_message: 'Use the recipe-pal agent to plan dinner', examples: ['Something vegetarian', 'Use what is in my fridge'], guide_path: '~/.claude/agents/recipe-pal/HOW-TO-USE.md' }]);
  await page.waitForSelector('.howto');
  check(await page.locator('.checklist').count() === 1, 'progress updated in place');
  check(await page.locator('.checklist li.done').count() === 2, 'progress shows both done');
  await ctx.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.click('.howto .first .copy');
  check((await page.evaluate(() => navigator.clipboard.readText())) === 'Use the recipe-pal agent to plan dinner', 'copy button copies first message');
  send([{ type: 'phase', step: 6, label: 'Tests' }, { type: 'tests', cases: [{ id: 'T1', name: 'Everyday', status: 'pass' }, { id: 'T2', name: 'Tricky', status: 'running' }] }]);
  await page.waitForSelector('.tiles');
  send([{ type: 'tests', cases: [{ id: 'T1', name: 'Everyday', status: 'pass' }, { id: 'T2', name: 'Tricky', status: 'fail', detail: 'Too long' }] }]);
  await page.waitForSelector('.tsum:has-text("1 of 2 passed")');
  check(await page.locator('.tiles').count() === 1, 'tests updated in place');
  execFileSync('python3', [SKILL + '/scripts/render_test_report.py', EX + '/tests/test-results.json', OUT + '/report.html']);
  send([{ type: 'report', html_path: OUT + '/report.html' }, { type: 'test_case_form', id: 'tc', text: 'Want to add your own test?' }]);
  await page.waitForSelector('#tcIn');
  await page.fill('#tcIn', 'Dinner for 2 with no oven'); await page.fill('#tcOut', 'it should suggest a stovetop recipe');
  await page.click('button:has-text("Add this test")');
  await expectEvent('test_case', e => e.input.includes('no oven'));
  send([{ type: 'done', title: 'Recipe Pal is ready', items: ['Installed for you', '7 of 7 tests passed'] }]);
  await page.waitForSelector('.b-done');
  await page.screenshot({ path: OUT + '/5-done.png', fullPage: false });

  // 13. reload: everything replays
  const before = await page.locator('.blk').count();
  await page.reload(); await page.waitForSelector('.b-done');
  const after = await page.locator('.blk').count();
  check(before === after, `reload replays the same blocks (${before} vs ${after})`);
  check((await page.locator('#acard').innerText()).includes('Recipe Pal'), 'card restored after reload');

  // 14. menu command
  await page.click('#menuBtn'); await page.click('text=Continue in chat instead');
  await expectEvent('command', e => e.name === 'switch_to_chat');

  // 15. phone layout + dark theme
  const ph = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  await ph.goto(url); await ph.waitForSelector('.b-done');
  const overflow = await ph.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  check(!overflow, 'no horizontal scroll on phone');
  await ph.click('#cardToggle'); await ph.waitForTimeout(400);
  await ph.screenshot({ path: OUT + '/6-phone-card.png' });
  await ph.close();

  // 16. no speech support → mic hidden, typing hint
  const ctx2 = await browser.newContext();
  await ctx2.addInitScript('delete window.SpeechRecognition; delete window.webkitSpeechRecognition;');
  const p2 = await ctx2.newPage(); await p2.goto(url); await p2.waitForSelector('.b-done');
  check(await p2.locator('#mic').isHidden(), 'mic hidden without speech support');
  check((await p2.locator('#status').innerText()).includes('Typing works'), 'fallback note shown');
  await ctx2.close();

  // 17. bad token is refused
  const bad = await (await fetch(url.replace(/t=[^&]+/, 't=wrong'))).status;
  check(bad === 403, 'wrong token refused');

  // 18. end
  send([{ type: 'end', text: 'Continue in your Claude Code window.' }]);
  await page.waitForSelector('#input:disabled');
  check(true, 'composer disabled at end');

  // 19. demo mode as a file
  const p3 = await browser.newPage({ viewport: { width: 1280, height: 820 } });
  await p3.goto('file://' + SKILL + '/assets/builder-template.html');
  await p3.waitForSelector('text=How should it sound?');
  await p3.screenshot({ path: OUT + '/7-demo.png' });

  // 20. stop, resume: same session, page replays everything
  cli('stop');
  const res = JSON.parse(cli('start', '--resume'));
  check(res.resumed && res.session_id === start.session_id && res.agent === 'Recipe Pal', 'resume reopens the same session');
  const p4 = await browser.newPage(); await p4.goto(res.url); await p4.waitForSelector('.b-done');
  check(await p4.locator('#input').isDisabled(), 'ended session stays ended after resume');
  check((await p4.locator('.blk').count()) >= before, 'resumed page replays the whole session');
  // a brand-new session stops the old server
  const fresh = JSON.parse(cli('start'));
  check(fresh.session_id !== start.session_id && !fresh.resumed, 'new session created');
  let oldDown = false; try { await fetch(res.url); } catch (e) { oldDown = true; }
  check(oldDown, 'old server stopped when a new session starts');

  const tr = execFileSync('python3', [SRV, '--home', HOME, '--session', start.session_id, 'transcript'], { encoding: 'utf8' });
  check(tr.includes('Recipe Pal') && tr.includes('User (spoken): a recipe helper for my family'), 'transcript includes card and spoken answer');
  fs.writeFileSync(OUT + '/transcript.txt', tr);

  check(errors.length === 0, 'no page errors: ' + JSON.stringify(errors));
  await browser.close();
  cli('stop');
  console.log(`\nScreenshots and transcript: ${OUT}`);
  console.log(failures ? `${failures} FAILED` : 'ALL PASSED');
  process.exit(failures ? 1 : 0);
})().catch(e => { console.error(e); try { cli('stop'); } catch (_) {} process.exit(1); });
