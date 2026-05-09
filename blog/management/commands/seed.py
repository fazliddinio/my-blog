from django.core.management.base import BaseCommand
from blog.models import (
    Post, Project, UsesCategory, UsesItem, Product, ProductBullet,
    NewsletterIssue, TimelineEntry,
)


class Command(BaseCommand):
    help = 'Seed the database with sample content from the HTML prototype'

    def handle(self, *args, **options):
        self.seed_posts()
        self.seed_projects()
        self.seed_uses()
        self.seed_products()
        self.seed_newsletter_issues()
        self.seed_timeline()
        self.stdout.write(self.style.SUCCESS('Database seeded successfully.'))

    def seed_posts(self):
        posts_data = [
            {
                'slug': 'notes-on-caching',
                'date': '2026-04-12',
                'title_en': 'Notes on caching, in three parts',
                'title_uz': 'Keshlash haqida eslatmalar, uch qismda',
                'dek_en': "The first version was a Map with a TTL. The third is the one I'd write from scratch today, and it's the one this post is about.",
                'dek_uz': "Birinchi versiya \u2014 TTL'li Map edi. Uchinchisi \u2014 bugun noldan yozadigan versiyam, va shu post aynan u haqida.",
                'tag': 'caching',
                'read_time': 8,
                'featured': True,
                'content_en': """<p>I've shipped maybe a dozen caches in my career \u2014 and I've thrown out at least nine of them. Each one taught me something about what I should have done instead. This essay is the version of that knowledge I'd hand to a younger me, before they wrote the first <code>Map</code>.</p>

<h2>The naive version</h2>
<p>It's the version everyone writes first, and for good reason: most of the time, it's enough. A <code>Map</code> with a TTL fallback. About fifteen lines of code, including the imports.</p>

<div class="code-block">
  <div class="code-block__header">
    <span class="code-block__file">cache.ts</span>
    <button class="code-block__copy">Copy</button>
  </div>
  <pre><span class="syn-comment">// A Map with a TTL fallback. That's it.</span>
<span class="syn-keyword">export</span> <span class="syn-keyword">const</span> <span class="syn-function">cache</span> = (ttl: <span class="syn-type">number</span>) => {
  <span class="syn-keyword">const</span> store = <span class="syn-keyword">new</span> <span class="syn-type">Map</span>&lt;<span class="syn-type">string</span>, { v: <span class="syn-type">unknown</span>; until: <span class="syn-type">number</span> }&gt;();
  <span class="syn-keyword">return</span> {
    <span class="syn-function">get</span>(k: <span class="syn-type">string</span>) {
      <span class="syn-keyword">const</span> hit = store.<span class="syn-function">get</span>(k);
      <span class="syn-keyword">if</span> (!hit) <span class="syn-keyword">return</span> <span class="syn-literal">undefined</span>;
      <span class="syn-keyword">if</span> (hit.until &lt; <span class="syn-type">Date</span>.<span class="syn-function">now</span>()) { store.<span class="syn-function">delete</span>(k); <span class="syn-keyword">return</span> <span class="syn-literal">undefined</span>; }
      <span class="syn-keyword">return</span> hit.v;
    },
    <span class="syn-function">set</span>(k: <span class="syn-type">string</span>, v: <span class="syn-type">unknown</span>) {
      store.<span class="syn-function">set</span>(k, { v, until: <span class="syn-type">Date</span>.<span class="syn-function">now</span>() + ttl });
    },
  };
};</pre>
</div>

<p>This works for everything that fits in memory and doesn't need to survive a restart. Which, in practice, is most of what I write. The interesting question is what happens when it doesn't.</p>

<h2>Where it breaks</h2>
<p>It breaks the first time you have two processes. It breaks the second time you have one process and a really hot key. It breaks the third time you forget to evict on write. And so on \u2014 the breakages compound.</p>""",
                'content_uz': """<p>Karyeram davomida o\u2018ntacha kesh yetkazgandirman \u2014 va kamida to\u2018qqiztasini chiqarib tashlaganman. Har biri menga nima qilishim kerakligini o\u2018rgatdi. Bu esse \u2014 yoshroq o\u2018zimga, birinchi <code>Map</code>\u2019ni yozishidan oldin uzatadigan bilim versiyam.</p>

<h2>Sodda versiya</h2>
<p>Bu \u2014 hamma birinchi yozadigan versiya, va sababi ham bor: ko\u2018p hollarda u yetarli. <code>Map</code> va TTL bilan. Importlarni qo\u2018shganda taxminan o\u2018n besh qator kod.</p>

<div class="code-block">
  <div class="code-block__header">
    <span class="code-block__file">cache.ts</span>
    <button class="code-block__copy">Copy</button>
  </div>
  <pre><span class="syn-comment">// A Map with a TTL fallback. That's it.</span>
<span class="syn-keyword">export</span> <span class="syn-keyword">const</span> <span class="syn-function">cache</span> = (ttl: <span class="syn-type">number</span>) => {
  <span class="syn-keyword">const</span> store = <span class="syn-keyword">new</span> <span class="syn-type">Map</span>&lt;<span class="syn-type">string</span>, { v: <span class="syn-type">unknown</span>; until: <span class="syn-type">number</span> }&gt;();
  <span class="syn-keyword">return</span> {
    <span class="syn-function">get</span>(k: <span class="syn-type">string</span>) {
      <span class="syn-keyword">const</span> hit = store.<span class="syn-function">get</span>(k);
      <span class="syn-keyword">if</span> (!hit) <span class="syn-keyword">return</span> <span class="syn-literal">undefined</span>;
      <span class="syn-keyword">if</span> (hit.until &lt; <span class="syn-type">Date</span>.<span class="syn-function">now</span>()) { store.<span class="syn-function">delete</span>(k); <span class="syn-keyword">return</span> <span class="syn-literal">undefined</span>; }
      <span class="syn-keyword">return</span> hit.v;
    },
    <span class="syn-function">set</span>(k: <span class="syn-type">string</span>, v: <span class="syn-type">unknown</span>) {
      store.<span class="syn-function">set</span>(k, { v, until: <span class="syn-type">Date</span>.<span class="syn-function">now</span>() + ttl });
    },
  };
};</pre>
</div>

<p>Bu xotiraga sig\u2018adigan va qayta ishga tushishdan keyin saqlanishi shart bo\u2018lmagan hamma narsa uchun ishlaydi. Amalda men yozadigan ishlarning ko\u2018pchiligi shunday. Qiziq savol \u2014 bu shartlar buzilganda nima bo\u2018ladi.</p>

<h2>Qayerda buziladi</h2>
<p>Birinchi marta ikkita jarayon paydo bo\u2018lganda buziladi. Ikkinchi marta bitta jarayon va juda qaynoq kalit bo\u2018lganda buziladi. Uchinchi marta yozishda evict qilishni unutganda buziladi. Va hokazo \u2014 buzilishlar to\u2018planib boradi.</p>""",
            },
            {
                'slug': 'i-stopped-reaching-for-redux',
                'date': '2026-03-28',
                'title_en': 'I stopped reaching for Redux',
                'title_uz': 'Men Redux\u2019ga qo\u2018l urishni to\u2018xtatdim',
                'dek_en': 'And what I reach for instead, depending on the size of the app and the patience of the team.',
                'dek_uz': 'Va uning o\u2018rniga nimani tanlayman \u2014 ilovaning hajmi va jamoaning sabriga qarab.',
                'tag': 'react', 'read_time': 12, 'featured': True,
                'content_en': '<p>Redux taught me a lot. But somewhere around 2023, I stopped reaching for it first. This post explains why, and what I use instead.</p>',
                'content_uz': '<p>Redux menga ko\u2018p narsa o\u2018rgatdi. Lekin 2023-yil atrofida uni birinchi navbatda tanlashni to\u2018xtatdim.</p>',
            },
            {
                'slug': 'tinyq-200-line-task-queue',
                'date': '2026-03-04',
                'title_en': 'How I built a 200-line task queue',
                'title_uz': '200 qatorlik vazifa navbatini qanday yozdim',
                'dek_en': 'Backed by SQLite. No Redis, no servers, no regrets \u2014 yet.',
                'dek_uz': 'SQLite asosida. Redis yo\u2018q, server yo\u2018q, afsus yo\u2018q \u2014 hozircha.',
                'tag': 'sqlite', 'read_time': 6, 'featured': True,
                'content_en': '<p>Sometimes you need a task queue but you don\'t need Redis. This is the story of building one in 200 lines of TypeScript.</p>',
                'content_uz': '<p>Ba\u2019zan sizga vazifa navbati kerak, lekin Redis kerak emas. Bu 200 qator TypeScript\u2019da uni yaratish hikoyasi.</p>',
            },
            {
                'slug': 'the-cost-of-a-yes',
                'date': '2026-02-14',
                'title_en': 'The cost of a yes',
                'title_uz': '"Ha"ning narxi',
                'dek_en': 'On agreeing to one more thing, and the small price you pay every time.',
                'dek_uz': 'Yana bir ishga rozilik berish, va har gal to\u2018laydigan kichik haqingiz haqida.',
                'tag': 'career', 'read_time': 4, 'featured': False,
                'content_en': '<p>Every yes is a no to something else. This essay is about recognizing the trade-off before it compounds.</p>',
                'content_uz': '<p>Har bir "ha" \u2014 boshqa narsaga "yo\u2018q". Bu esse \u2014 kelishuv to\u2018planib borishidan oldin uni anglash haqida.</p>',
            },
            {
                'slug': 'postgres-as-everything',
                'date': '2026-01-22',
                'title_en': 'Postgres as everything',
                'title_uz': 'Postgres \u2014 hamma narsa o\u2018rnida',
                'dek_en': 'Queue, search, pubsub, blob store. Where it falls down and where it surprised me.',
                'dek_uz': 'Navbat, qidiruv, pubsub, fayl saqlash. Qayerda yiqilganini va qayerda meni hayron qoldirganini.',
                'tag': 'postgres', 'read_time': 14, 'featured': False,
                'content_en': '<p>Postgres can do a lot more than most people think. Here is where it shines and where it falls short.</p>',
                'content_uz': '<p>Postgres ko\u2018p odamlar o\u2018ylaganidan ko\u2018proq narsa qila oladi.</p>',
            },
            {
                'slug': 'one-year-of-side-projects',
                'date': '2025-12-30',
                'title_en': 'One year of side projects',
                'title_uz': 'Bir yillik yondosh loyihalar',
                'dek_en': "Twelve things I shipped, three I didn't, and one I shouldn't have.",
                'dek_uz': "Yetkazganim o\u2018n ikki narsa, yetkazmaganim uchtasi, va yetkazmasligim kerak bo\u2018lgani bittasi.",
                'tag': 'meta', 'read_time': 9, 'featured': False,
                'content_en': '<p>A review of everything I built and shipped in 2025.</p>',
                'content_uz': '<p>2025-yilda yaratgan va yetkazgan hamma narsalarning sharhi.</p>',
            },
            {
                'slug': 'a-small-rewrite',
                'date': '2025-11-08',
                'title_en': 'A small rewrite',
                'title_uz': 'Kichik bir qayta yozish',
                'dek_en': 'In which I delete 4,000 lines and the app gets faster.',
                'dek_uz': 'Bunda men 4 000 qatorni o\u2018chiraman va ilova tezroq ishlay boshlaydi.',
                'tag': 'refactor', 'read_time': 7, 'featured': False,
                'content_en': '<p>The best code is the code you delete.</p>',
                'content_uz': '<p>Eng yaxshi kod \u2014 o\u2018chirib tashlagan kodingiz.</p>',
            },
            {
                'slug': 'on-leaving-a-job-well',
                'date': '2025-09-15',
                'title_en': 'On leaving a job well',
                'title_uz': 'Ishdan chiroyli ketish haqida',
                'dek_en': "What I wish I'd known about transitions, and the four-week version of doing it right.",
                'dek_uz': "O\u2018tish davri haqida bilishni istagan narsalarim va to\u2018g\u2018ri qilishning to\u2018rt haftalik versiyasi.",
                'tag': 'career', 'read_time': 11, 'featured': False,
                'content_en': '<p>Leaving well is a skill. Here is a four-week playbook.</p>',
                'content_uz': '<p>Yaxshi ketish \u2014 bu mahorat. Mana to\u2018rt haftalik reja.</p>',
            },
        ]

        for p in posts_data:
            Post.objects.update_or_create(slug=p['slug'], defaults=p)
        self.stdout.write(f'  Created {len(posts_data)} posts')

    def seed_projects(self):
        projects_data = [
            {'name': 'tinyq', 'tagline_en': 'A 200-line task queue, backed by SQLite.', 'tagline_uz': 'SQLite\u2019ga asoslangan 200 qatorlik vazifa navbati.', 'desc_en': 'No Redis, no servers. Designed for personal projects that need to run a job once a minute.', 'desc_uz': 'Redis ham, server ham yo\u2018q. Daqiqada bir marta vazifa bajaradigan shaxsiy loyihalar uchun.', 'stars': 1247, 'language': 'TypeScript', 'href': 'https://github.com/fazliddin/tinyq', 'order': 0},
            {'name': 'paper-cuts', 'tagline_en': 'Find the slow paths in your Postgres app.', 'tagline_uz': 'Postgres ilovangizdagi sekin yo\u2018llarni toping.', 'desc_en': 'A small CLI that watches `pg_stat_statements` and tells you what to fix first.', 'desc_uz': '`pg_stat_statements`ni kuzatadigan va birinchi navbatda nimani tuzatish kerakligini aytadigan kichik CLI.', 'stars': 412, 'language': 'Go', 'href': 'https://github.com/fazliddin/paper-cuts', 'order': 1},
            {'name': 'colormath', 'tagline_en': 'Color-space conversions with friendly types.', 'tagline_uz': 'Qulay tiplarga ega rang fazosi konvertatsiyalari.', 'desc_en': 'OKLCH-aware, no opinions about your design system. Used in three of my projects.', 'desc_uz': 'OKLCH bilan ishlaydi, dizayn tizimingizga aralashmaydi. Mening uch loyihamda ishlatilgan.', 'stars': 89, 'language': 'TypeScript', 'href': 'https://github.com/fazliddin/colormath', 'order': 2},
            {'name': 'feed-up', 'tagline_en': 'A two-file RSS reader for one user.', 'tagline_uz': 'Bir foydalanuvchi uchun ikki fayllik RSS o\u2018qigich.', 'desc_en': 'Single SQLite file, one HTML page. Runs on a $4/mo VPS and sends me a daily digest.', 'desc_uz': 'Yagona SQLite fayl, bitta HTML sahifa. $4/oy VPS\u2019da ishlaydi va menga kunlik dayjest yuboradi.', 'stars': 326, 'language': 'Python', 'href': 'https://github.com/fazliddin/feed-up', 'order': 3},
            {'name': 'note-of-the-day', 'tagline_en': "A daily prompt to write *something*.", 'tagline_uz': 'Har kuni *biror narsa* yozishga undov.', 'desc_en': 'iOS Shortcut + a tiny server. Has gotten me to write 600 days in a row.', 'desc_uz': 'iOS Shortcut + kichik server. Meni 600 kun ketma-ket yozishga majbur qildi.', 'stars': 58, 'language': 'Swift', 'href': 'https://github.com/fazliddin/note-of-the-day', 'order': 4},
            {'name': 'fazliddin-blog', 'tagline_en': 'The static site you are reading right now.', 'tagline_uz': 'Hozir o\u2018qib turgan statik saytingiz.', 'desc_en': 'Markdown in, HTML out. About 800 lines of build script.', 'desc_uz': 'Kirishda Markdown, chiqishda HTML. Taxminan 800 qator build skripti.', 'stars': 31, 'language': 'TypeScript', 'href': 'https://github.com/fazliddin/fazliddin-blog', 'order': 5},
        ]
        for p in projects_data:
            Project.objects.update_or_create(name=p['name'], defaults=p)
        self.stdout.write(f'  Created {len(projects_data)} projects')

    def seed_uses(self):
        uses_data = [
            ('Editor', 'Muharrir', 0, [
                ('Neovim', 'Five years in. The config is shorter than my Vim config was.', 'Besh yil bo\u2018ldi. Konfig avvalgi Vim konfigimdan qisqaroq.'),
                ('Helix', 'For everything that is not Neovim. Modal, ergonomic.', 'Neovim emas hamma narsa uchun. Modal, ergonomik.'),
                ('VS Code', 'When pairing. Fine.', 'Juftlikda ishlaganda. Yaxshi.'),
            ]),
            ('Terminal', 'Terminal', 1, [
                ('Ghostty', 'Fast. Sensible defaults.', 'Tez. Aqlli sukut sozlamalari.'),
                ('fish', 'No regrets, despite what your dotfiles think.', 'Afsuslanmadim, dotfile\u2019laringiz nima deb o\u2018ylasa ham.'),
                ('eza \u00b7 bat \u00b7 fd \u00b7 rg', 'The usual upgrades.', 'Odatdagi yangilanishlar.'),
            ]),
            ('Languages', 'Tillar', 2, [
                ('TypeScript', 'For the front end and most of the back end.', 'Frontend va backend\u2019ning ko\u2018p qismi uchun.'),
                ('Go', 'When something needs a single binary and a tight loop.', 'Yagona binar va tezkor sikl kerak bo\u2018lganda.'),
                ('Python', 'For scripts that will outlive me.', 'Mendan ko\u2018proq yashaydigan skriptlar uchun.'),
            ]),
            ('Hardware', 'Jihozlar', 3, [
                ('MacBook Pro 14"', 'M-something. Fine. Sleep mostly works.', 'M-nimadir. Yaxshi. Sleep ko\u2018pincha ishlaydi.'),
                ('Keychron Q1', 'Browns. Loud enough to annoy me, quiet enough to ship.', 'Browns. Meni bezdiradigan darajada baland, ish bitiradigan darajada past.'),
                ('Dell U2723QE', 'One monitor, never two.', 'Bitta monitor, hech qachon ikkita emas.'),
            ]),
        ]
        for title_en, title_uz, order, items in uses_data:
            cat, _ = UsesCategory.objects.update_or_create(
                title_en=title_en, defaults={'title_uz': title_uz, 'order': order}
            )
            for i, (name, note_en, note_uz) in enumerate(items):
                UsesItem.objects.update_or_create(
                    category=cat, name=name,
                    defaults={'note_en': note_en, 'note_uz': note_uz, 'order': i}
                )
        self.stdout.write(f'  Created {len(uses_data)} uses categories')

    def seed_products(self):
        products_data = [
            {
                'slug': 'engineers-writing-kit',
                'name_en': 'The Engineer\u2019s Writing Kit', 'name_uz': 'Muhandis uchun yozish to\u2018plami',
                'kind_en': 'Course', 'kind_uz': 'Kurs',
                'price_en': '$120', 'price_uz': '$120',
                'blurb_en': 'A four-week course on writing essays without sounding like a marketing email.', 'blurb_uz': 'Marketing xatiga o\u2018xshamaydigan esselar yozish bo\u2018yicha to\u2018rt haftalik kurs.',
                'cta_en': 'Enroll', 'cta_uz': 'Yozilish', 'order': 0,
                'content_en': """<section class="product-hero">
<h1>The Engineer\u2019s Writing Kit</h1>
<p class="lead">A four-week course that teaches engineers how to write essays, docs, and blog posts that people actually want to read \u2014 without sounding like a marketing email or a corporate memo.</p>
</section>

<section class="product-section">
<h2>What you\u2019ll learn</h2>
<p>Most engineers can write code that communicates intent. But when it comes to prose \u2014 blog posts, documentation, internal memos, RFCs \u2014 we default to either bone-dry technical writing or overly casual stream-of-consciousness. Neither lands well.</p>
<p>This course teaches you to find your voice, structure your ideas, and edit with precision. You\u2019ll write four real essays during the course and get feedback on every one of them from me and a small cohort of peers.</p>
<p>By the end, you\u2019ll have a repeatable process for going from \u201cI have a vague idea\u201d to \u201cI published something I\u2019m proud of\u201d \u2014 in hours, not weeks.</p>
</section>

<section class="product-section">
<h2>Curriculum overview</h2>
<div class="curriculum">
<div class="curriculum-week">
<h3>Week 1: Finding your voice</h3>
<p>We start by reading five essays that work \u2014 and dissecting why. You\u2019ll identify the writing tics that make technical prose feel flat (passive voice, hedge words, unnecessary abstractions) and practice rewriting real examples. Your first assignment: a 500-word essay on something you built recently, written as if you\u2019re explaining it to a friend over coffee.</p>
</div>
<div class="curriculum-week">
<h3>Week 2: Structure and rhythm</h3>
<p>Good writing has a shape. This week covers the anatomy of an essay: openers that hook, paragraphs that flow, transitions that don\u2019t clunk. We\u2019ll study the inverted pyramid, the narrative arc, and the \u201cshow-then-tell\u201d pattern that works especially well for technical content. Assignment: restructure a draft you\u2019ve been sitting on.</p>
</div>
<div class="curriculum-week">
<h3>Week 3: Editing ruthlessly</h3>
<p>First drafts are supposed to be messy. The skill is in the edit. This week you\u2019ll learn to cut 30% of your word count without losing meaning, spot sentences that are doing no work, and develop an eye for rhythm at the sentence level. We\u2019ll do live editing sessions where I rewrite paragraphs in real time and explain every decision.</p>
</div>
<div class="curriculum-week">
<h3>Week 4: Publishing and feedback</h3>
<p>The last mile: titles, deks, meta descriptions, and the psychology of hitting \u201cPublish.\u201d We\u2019ll cover distribution basics (where to post, how to build an audience of 1,000 readers), and you\u2019ll publish your final essay to the real internet. Then we do a group critique session and celebrate.</p>
</div>
</div>
</section>

<section class="product-section">
<h2>What past students say</h2>
<blockquote>
<p>\u201cI\u2019d been blogging for three years but never felt confident about my writing. After this course, I published an essay that got to the front page of Hacker News. The editing framework alone was worth the price.\u201d</p>
<footer>\u2014 Sarah K., Staff Engineer at Stripe</footer>
</blockquote>
<blockquote>
<p>\u201cFazliddin doesn\u2019t teach you formulas. He teaches you to hear your own writing. I write internal docs differently now \u2014 my team actually reads them.\u201d</p>
<footer>\u2014 Marco R., Engineering Manager</footer>
</blockquote>
<blockquote>
<p>\u201cThe cohort feedback was the best part. Having five other engineers read your draft and tell you where they got bored is brutally useful.\u201d</p>
<footer>\u2014 Priya M., Senior Developer</footer>
</blockquote>
</section>

<section class="product-section">
<h2>Frequently asked questions</h2>
<div class="faq">
<details>
<summary>Do I need prior writing experience?</summary>
<p>No. If you can write a clear pull request description, you have enough skill to start. The course meets you where you are.</p>
</details>
<details>
<summary>How much time does it take per week?</summary>
<p>Plan for about 3\u20134 hours: one hour of lessons, one hour of reading, and 1\u20132 hours of writing. It\u2019s designed to fit alongside a full-time job.</p>
</details>
<details>
<summary>Is there a refund policy?</summary>
<p>Yes. If you complete Week 1 and decide it\u2019s not for you, email me and I\u2019ll refund you in full, no questions asked.</p>
</details>
<details>
<summary>When does the next cohort start?</summary>
<p>Cohorts run every 6\u20138 weeks. Join the waitlist and you\u2019ll be notified 2 weeks before the next one opens.</p>
</details>
</div>
</section>""",
                'content_uz': """<section class="product-hero">
<h1>Muhandis uchun yozish to\u2018plami</h1>
<p class="lead">To\u2018rt haftalik kurs \u2014 muhandislarga odamlar chindan o\u2018qimoqchi bo\u2018lgan esselar, hujjatlar va blog postlarini yozishni o\u2018rgatadi. Marketing xati yoki korporativ xatga o\u2018xshamasdan.</p>
</section>

<section class="product-section">
<h2>Nimalarni o\u2018rganasiz</h2>
<p>Ko\u2018pchilik muhandislar maqsadni ifodalovchi kod yoza oladi. Lekin nasr yozishga kelganda \u2014 blog postlar, hujjatlar, ichki xatlar, RFC \u2014 biz yo quruq texnik yozuvga, yo haddan tashqari erkin oqim uslubiga o\u2018tamiz. Ikkalasi ham yaxshi qabul qilinmaydi.</p>
<p>Bu kurs sizga o\u2018z ovozingizni topish, fikrlaringizni tuzish va aniqlik bilan tahrir qilishni o\u2018rgatadi. Kurs davomida to\u2018rtta haqiqiy esse yozasiz va har biriga men va kichik guruh a\u2019zolaridan fikr-mulohaza olasiz.</p>
<p>Yakunida sizda \u201cMenda noaniq fikr bor\u201d dan \u201cMen faxrlanadigan narsa nashr qildim\u201d ga o\u2018tishning takrorlanadigan jarayoni bo\u2018ladi \u2014 haftalar emas, soatlar ichida.</p>
</section>

<section class="product-section">
<h2>O\u2018quv dasturi</h2>
<div class="curriculum">
<div class="curriculum-week">
<h3>1-hafta: O\u2018z ovozingizni topish</h3>
<p>Biz ishlaydigan beshta esseni o\u2018qish va nima uchun ishlashini tahlil qilishdan boshlaymiz. Texnik nasrni tekis qiladigan yozish odatlarini (passiv ovoz, ikkilanish so\u2018zlari, keraksiz abstraktsiyalar) aniqlaysiz va haqiqiy misollarni qayta yozishni mashq qilasiz. Birinchi topshiriq: yaqinda yaratgan narsangiz haqida 500 so\u2018zlik esse, xuddi do\u2018stingizga kofe ustida tushuntirayotgandek yozing.</p>
</div>
<div class="curriculum-week">
<h3>2-hafta: Tuzilma va ritm</h3>
<p>Yaxshi yozuv shaklga ega. Bu hafta esse anatomiyasini o\u2018rganamiz: qiziqtiradigan ochilishlar, oqadigan paragraflar, g\u2018alati eshitilmaydigan o\u2018tishlar. Teskari piramida, narrativ yoy va texnik kontent uchun ayniqsa yaxshi ishlaydigan \u201cko\u2018rsat-keyin-ayt\u201d naqshini o\u2018rganamiz. Topshiriq: yotgan qoralamangizni qayta tuzing.</p>
</div>
<div class="curriculum-week">
<h3>3-hafta: Shafqatsiz tahrir</h3>
<p>Birinchi qoralamalar tartibsiz bo\u2018lishi kerak. Mahorat \u2014 tahrirda. Bu hafta so\u2018z sonining 30% ini ma\u2019nosini yo\u2018qotmasdan qisqartirishni, hech qanday ish qilmayotgan jumlalarni topishni va jumla darajasida ritmni sezishni o\u2018rganasiz. Men real vaqtda paragraflarni qayta yozadigan va har bir qarorni tushuntiradigan jonli tahrir sessiyalari o\u2018tkazamiz.</p>
</div>
<div class="curriculum-week">
<h3>4-hafta: Nashr qilish va fikr-mulohaza</h3>
<p>Oxirgi bosqich: sarlavhalar, deklar, meta tavsiflar va \u201cNashr qilish\u201d tugmasini bosish psixologiyasi. Tarqatish asoslarini (qayerga joylashtirish, 1000 o\u2018quvchili auditoriyani qanday yaratish) ko\u2018rib chiqamiz va siz yakuniy essengizni haqiqiy internetga nashr qilasiz. Keyin guruh tanqidi sessiyasi o\u2018tkazamiz va nishonlaymiz.</p>
</div>
</div>
</section>

<section class="product-section">
<h2>O\u2018tgan talabalar nima deydi</h2>
<blockquote>
<p>\u201cUch yildan beri blog yozardim, lekin yozuvimga hech ishonchim yo\u2018q edi. Bu kursdan keyin Hacker News bosh sahifasiga chiqqan esse nashr qildim. Faqat tahrir frameworki ham narxiga arziydi.\u201d</p>
<footer>\u2014 Sarah K., Stripe\u2019da Staff Engineer</footer>
</blockquote>
<blockquote>
<p>\u201cFazliddin sizga formulalar o\u2018rgatmaydi. U sizga o\u2018z yozuvingizni eshitishni o\u2018rgatadi. Endi ichki hujjatlarni boshqacha yozaman \u2014 jamoam ularni chindan o\u2018qiydi.\u201d</p>
<footer>\u2014 Marco R., Engineering Manager</footer>
</blockquote>
<blockquote>
<p>\u201cGuruh fikr-mulohazasi eng yaxshi qism edi. Beshta boshqa muhandisning qoralamangizni o\u2018qib, qayerda zerikkanini aytishi juda foydali.\u201d</p>
<footer>\u2014 Priya M., Senior Developer</footer>
</blockquote>
</section>

<section class="product-section">
<h2>Ko\u2018p beriladigan savollar</h2>
<div class="faq">
<details>
<summary>Oldingi yozish tajribasi kerakmi?</summary>
<p>Yo\u2018q. Agar aniq pull request tavsifi yoza olsangiz, boshlash uchun yetarli ko\u2018nikma bor. Kurs sizning darajangizga moslashadi.</p>
</details>
<details>
<summary>Haftasiga qancha vaqt ketadi?</summary>
<p>Taxminan 3\u20134 soat rejalashtiring: bir soat darslar, bir soat o\u2018qish va 1\u20132 soat yozish. To\u2018liq ish kuniga mos keladigan qilib yaratilgan.</p>
</details>
<details>
<summary>Pul qaytarish siyosati bormi?</summary>
<p>Ha. Agar 1-haftani tugatib, bu siz uchun emasligiga qaror qilsangiz, menga xat yozing va men sizga to\u2018liq pulni hech qanday savolsiz qaytaraman.</p>
</details>
<details>
<summary>Keyingi guruh qachon boshlanadi?</summary>
<p>Guruhlar har 6\u20138 haftada ishlaydi. Kutish ro\u2018yxatiga qo\u2018shiling va keyingisi ochilishidan 2 hafta oldin xabar olasiz.</p>
</details>
</div>
</section>""",
                'bullets': [
                    ('Eight lessons + four assignments', 'Sakkiz dars + to\u2018rt topshiriq'),
                    ('Private cohort feedback', 'Yopiq guruh fikrlari'),
                    ('Lifetime access to updates', 'Yangilanishlarga umrbod kirish'),
                ],
            },
            {
                'slug': 'tinyq-pro',
                'name_en': 'tinyq Pro', 'name_uz': 'tinyq Pro',
                'kind_en': 'SaaS', 'kind_uz': 'SaaS',
                'price_en': '$12 / mo', 'price_uz': '$12 / oy',
                'blurb_en': 'Hosted version of my open-source task queue. For people who do not want to operate a database.', 'blurb_uz': 'Mening ochiq kodli vazifa navbatimning xosting versiyasi. Ma\u2019lumotlar bazasi bilan ishlashni xohlamaganlar uchun.',
                'cta_en': 'Start free', 'cta_uz': 'Bepul boshlash', 'order': 1,
                'content_en': """<section class="product-hero">
<h1>tinyq Pro</h1>
<p class="lead">The hosted version of the open-source task queue you already love. No infrastructure to manage, no database to babysit. Just enqueue jobs and let tinyq handle the rest.</p>
</section>

<section class="product-section">
<h2>Features</h2>
<div class="features-grid">
<div class="feature">
<h3>Zero infrastructure</h3>
<p>No Redis, no Postgres, no Docker containers. Sign up, grab your API key, and start enqueuing. Your first job can be running in under two minutes.</p>
</div>
<div class="feature">
<h3>Drop-in replacement</h3>
<p>Already using the open-source tinyq? Point your client at our API endpoint instead of your local SQLite file. Same interface, same behavior, none of the ops burden.</p>
</div>
<div class="feature">
<h3>Real-time dashboard</h3>
<p>See every job in flight: pending, running, completed, failed. Filter by queue name, search by payload, and replay failed jobs with one click.</p>
</div>
<div class="feature">
<h3>Alerting built in</h3>
<p>Get notified via Email or Slack when jobs fail, when queues back up, or when your error rate crosses a threshold you define.</p>
</div>
<div class="feature">
<h3>Automatic retries</h3>
<p>Configure retry policies per queue: exponential backoff, linear delay, or custom intervals. Dead-letter queues catch jobs that exhaust all retries.</p>
</div>
<div class="feature">
<h3>End-to-end encryption</h3>
<p>Job payloads are encrypted at rest and in transit. Your data never touches our logs. SOC 2 Type II in progress.</p>
</div>
</div>
</section>

<section class="product-section">
<h2>Pricing</h2>
<div class="pricing-grid">
<div class="pricing-tier">
<h3>Free</h3>
<p class="pricing-price">$0 / mo</p>
<ul>
<li>100,000 jobs per month</li>
<li>1 queue</li>
<li>7-day job history</li>
<li>Community support</li>
</ul>
</div>
<div class="pricing-tier pricing-tier--featured">
<h3>Pro</h3>
<p class="pricing-price">$12 / mo</p>
<ul>
<li>Unlimited jobs</li>
<li>Unlimited queues</li>
<li>90-day job history</li>
<li>Email + Slack alerts</li>
<li>Priority support</li>
</ul>
</div>
<div class="pricing-tier">
<h3>Team</h3>
<p class="pricing-price">$49 / mo</p>
<ul>
<li>Everything in Pro</li>
<li>5 team members</li>
<li>365-day job history</li>
<li>SSO / SAML</li>
<li>Dedicated support channel</li>
</ul>
</div>
</div>
</section>

<section class="product-section">
<h2>Getting started</h2>
<p>Install the client library and start enqueuing jobs in three lines of code:</p>
<div class="code-block">
<div class="code-block__header">
<span class="code-block__file">worker.ts</span>
</div>
<pre>import { TinyQ } from "tinyq-pro";

const q = new TinyQ({ apiKey: process.env.TINYQ_API_KEY });

// Enqueue a job
await q.enqueue("emails", {
  to: "user@example.com",
  template: "welcome",
});

// Process jobs
q.process("emails", async (job) => {
  await sendEmail(job.data.to, job.data.template);
});</pre>
</div>
<p>That\u2019s it. The Pro API is identical to the open-source version \u2014 swap the import and the connection string and you\u2019re done.</p>
</section>

<section class="product-section">
<h2>How it compares</h2>
<table class="comparison-table">
<thead>
<tr><th></th><th>tinyq OSS</th><th>tinyq Pro</th><th>BullMQ + Redis</th><th>AWS SQS</th></tr>
</thead>
<tbody>
<tr><td>Setup time</td><td>2 min</td><td>1 min</td><td>15\u201330 min</td><td>10\u201320 min</td></tr>
<tr><td>Infrastructure</td><td>SQLite file</td><td>None (hosted)</td><td>Redis server</td><td>AWS account</td></tr>
<tr><td>Dashboard</td><td>None</td><td>Built in</td><td>Separate tool</td><td>CloudWatch</td></tr>
<tr><td>Cost at 500k jobs/mo</td><td>Free</td><td>$12/mo</td><td>~$15\u2013$50/mo</td><td>~$2\u2013$5/mo</td></tr>
<tr><td>Complexity</td><td>Minimal</td><td>Minimal</td><td>Moderate</td><td>High</td></tr>
</tbody>
</table>
</section>""",
                'content_uz': """<section class="product-hero">
<h1>tinyq Pro</h1>
<p class="lead">Siz allaqachon yaxshi ko\u2018rgan ochiq kodli vazifa navbatining xosting versiyasi. Boshqaradigan infratuzilma yo\u2018q, parvarishlash kerak bo\u2018lgan ma\u2019lumotlar bazasi yo\u2018q. Vazifalarni navbatga qo\u2018ying va qolganini tinyq\u2019ga qoldiring.</p>
</section>

<section class="product-section">
<h2>Xususiyatlar</h2>
<div class="features-grid">
<div class="feature">
<h3>Nol infratuzilma</h3>
<p>Redis yo\u2018q, Postgres yo\u2018q, Docker konteynerlar yo\u2018q. Ro\u2018yxatdan o\u2018ting, API kalitingizni oling va navbatga qo\u2018shishni boshlang. Birinchi vazifangiz ikki daqiqadan kamroq vaqtda ishlay boshlaydi.</p>
</div>
<div class="feature">
<h3>To\u2018g\u2018ridan-to\u2018g\u2018ri almashtirish</h3>
<p>Allaqachon ochiq kodli tinyq ishlatayapsizmi? Klientingizni mahalliy SQLite faylingiz o\u2018rniga bizning API endpoint\u2019imizga yo\u2018naltiring. Bir xil interfeys, bir xil xatti-harakat, operatsion yuk yo\u2018q.</p>
</div>
<div class="feature">
<h3>Real vaqt paneli</h3>
<p>Har bir vazifani ko\u2018ring: kutayotgan, ishlayotgan, tugallangan, muvaffaqiyatsiz. Navbat nomi bo\u2018yicha filtr qiling, payload bo\u2018yicha qidiring va muvaffaqiyatsiz vazifalarni bir marta bosish bilan qayta ishga tushiring.</p>
</div>
<div class="feature">
<h3>O\u2018rnatilgan bildirishnomalar</h3>
<p>Vazifalar muvaffaqiyatsiz bo\u2018lganda, navbatlar to\u2018lib ketganda yoki xato darajangiz siz belgilagan chegaradan oshganda Email yoki Slack orqali xabar oling.</p>
</div>
<div class="feature">
<h3>Avtomatik qayta urinishlar</h3>
<p>Har bir navbat uchun qayta urinish siyosatlarini sozlang: eksponensial kechikish, chiziqli kechikish yoki maxsus oraliqlar. Dead-letter navbatlari barcha urinishlarni tugallagan vazifalarni ushlaydi.</p>
</div>
<div class="feature">
<h3>Uchidan-uchiga shifrlash</h3>
<p>Vazifa ma\u2019lumotlari dam olish va uzatish paytida shifrlanadi. Ma\u2019lumotlaringiz bizning loglarimizga hech qachon tushmaydi. SOC 2 Type II jarayonda.</p>
</div>
</div>
</section>

<section class="product-section">
<h2>Narxlar</h2>
<div class="pricing-grid">
<div class="pricing-tier">
<h3>Bepul</h3>
<p class="pricing-price">$0 / oy</p>
<ul>
<li>Oyiga 100 000 vazifa</li>
<li>1 ta navbat</li>
<li>7 kunlik vazifa tarixi</li>
<li>Hamjamiyat yordami</li>
</ul>
</div>
<div class="pricing-tier pricing-tier--featured">
<h3>Pro</h3>
<p class="pricing-price">$12 / oy</p>
<ul>
<li>Cheksiz vazifalar</li>
<li>Cheksiz navbatlar</li>
<li>90 kunlik vazifa tarixi</li>
<li>Email + Slack bildirishnomalari</li>
<li>Ustuvor yordam</li>
</ul>
</div>
<div class="pricing-tier">
<h3>Jamoa</h3>
<p class="pricing-price">$49 / oy</p>
<ul>
<li>Pro\u2019dagi hamma narsa</li>
<li>5 ta jamoa a\u2019zosi</li>
<li>365 kunlik vazifa tarixi</li>
<li>SSO / SAML</li>
<li>Maxsus yordam kanali</li>
</ul>
</div>
</div>
</section>

<section class="product-section">
<h2>Boshlash</h2>
<p>Klient kutubxonasini o\u2018rnating va uch qator kodda vazifalarni navbatga qo\u2018shishni boshlang:</p>
<div class="code-block">
<div class="code-block__header">
<span class="code-block__file">worker.ts</span>
</div>
<pre>import { TinyQ } from "tinyq-pro";

const q = new TinyQ({ apiKey: process.env.TINYQ_API_KEY });

// Vazifani navbatga qo\u2018shish
await q.enqueue("emails", {
  to: "user@example.com",
  template: "welcome",
});

// Vazifalarni qayta ishlash
q.process("emails", async (job) => {
  await sendEmail(job.data.to, job.data.template);
});</pre>
</div>
<p>Hammasi shu. Pro API ochiq kodli versiya bilan bir xil \u2014 importni va ulanish satrini almashtiring va tayyor.</p>
</section>

<section class="product-section">
<h2>Solishtiruv</h2>
<table class="comparison-table">
<thead>
<tr><th></th><th>tinyq OSS</th><th>tinyq Pro</th><th>BullMQ + Redis</th><th>AWS SQS</th></tr>
</thead>
<tbody>
<tr><td>O\u2018rnatish vaqti</td><td>2 daq</td><td>1 daq</td><td>15\u201330 daq</td><td>10\u201320 daq</td></tr>
<tr><td>Infratuzilma</td><td>SQLite fayl</td><td>Yo\u2018q (xosting)</td><td>Redis server</td><td>AWS akkaunt</td></tr>
<tr><td>Panel</td><td>Yo\u2018q</td><td>O\u2018rnatilgan</td><td>Alohida vosita</td><td>CloudWatch</td></tr>
<tr><td>500k vazifa/oy narxi</td><td>Bepul</td><td>$12/oy</td><td>~$15\u2013$50/oy</td><td>~$2\u2013$5/oy</td></tr>
<tr><td>Murakkablik</td><td>Minimal</td><td>Minimal</td><td>O\u2018rtacha</td><td>Yuqori</td></tr>
</tbody>
</table>
</section>""",
                'bullets': [
                    ('Free tier: 100k jobs / mo', 'Bepul tarif: 100 ming vazifa / oy'),
                    ('Drop-in replacement for OSS tinyq', 'Ochiq tinyq o\u2018rniga to\u2018g\u2018ridan-to\u2018g\u2018ri qo\u2018yiladi'),
                    ('Email + Slack alerting', 'Email + Slack bildirishnomalari'),
                ],
            },
            {
                'slug': 'small-book-on-caching',
                'name_en': 'A Small Book on Caching', 'name_uz': 'Keshlash haqida kichik kitob',
                'kind_en': 'eBook', 'kind_uz': 'eKitob',
                'price_en': '$24', 'price_uz': '$24',
                'blurb_en': 'The post that started this site, expanded into 90 pages of patterns, traps, and code.', 'blurb_uz': 'Bu saytni boshlagan post, 90 sahifalik shablonlar, tuzoqlar va kod ko\u2018rinishida kengaytirilgan.',
                'cta_en': 'Buy the book', 'cta_uz': 'Kitobni sotib olish', 'order': 2,
                'content_en': """<section class="product-hero">
<h1>A Small Book on Caching</h1>
<p class="lead">Everything I know about caching, distilled into 90 pages. Patterns that work, traps that don\u2019t, and 24 worked examples in TypeScript. The blog post that started this site, expanded into something worth paying for.</p>
</section>

<section class="product-section">
<h2>Table of contents</h2>
<div class="toc">
<ol>
<li><strong>Chapter 1: The Map with a TTL</strong> \u2014 Why every cache starts here, and why most should stay here longer than you think.</li>
<li><strong>Chapter 2: Invalidation is the hard part</strong> \u2014 Write-through, write-behind, and the event-driven approach that actually works at scale.</li>
<li><strong>Chapter 3: Cache stampedes</strong> \u2014 What happens when a hundred requests hit an empty cache at once, and three ways to prevent it.</li>
<li><strong>Chapter 4: Layered caches</strong> \u2014 L1/L2 patterns for apps that need both speed and consistency. When to use Redis vs. an in-process Map.</li>
<li><strong>Chapter 5: Cache keys are a design decision</strong> \u2014 Naming conventions, versioning strategies, and the one mistake that will corrupt your data.</li>
<li><strong>Chapter 6: Measuring cache effectiveness</strong> \u2014 Hit ratios, latency percentiles, and how to know when your cache is hurting more than helping.</li>
<li><strong>Chapter 7: Caching at the edge</strong> \u2014 CDN caching, stale-while-revalidate, and the surprisingly tricky world of Cache-Control headers.</li>
<li><strong>Chapter 8: When not to cache</strong> \u2014 The cases where adding a cache makes everything worse. Recognizing them before you ship.</li>
</ol>
</div>
</section>

<section class="product-section">
<h2>Sample excerpt: Chapter 3</h2>
<blockquote class="book-excerpt">
<p>Imagine your cache key expires at 12:00:00. At 12:00:01, 200 requests arrive for the same resource. Each one sees a cache miss. Each one hits the database. The database, which was happily serving 10 queries per second, now gets 200 in one second. It slows down. The requests take longer. More requests pile up behind them. This is a cache stampede, and it has taken down more production systems than most engineers realize.</p>
<p>The fix is deceptively simple: only let one request through. Everyone else waits. The first request populates the cache, and the rest read from it. This is called \u201crequest coalescing\u201d or \u201csingle-flight,\u201d and implementing it correctly is the subject of this chapter.</p>
</blockquote>
</section>

<section class="product-section">
<h2>What readers are saying</h2>
<blockquote>
<p>\u201cThis is the caching book I wish I had five years ago. Concise, practical, and full of code I actually copied into production.\u201d</p>
<footer>\u2014 James L., Principal Engineer</footer>
</blockquote>
<blockquote>
<p>\u201cChapter 5 on cache keys alone saved me from a bug that would have taken days to track down. Worth every penny.\u201d</p>
<footer>\u2014 Aisha T., Backend Developer</footer>
</blockquote>
<blockquote>
<p>\u201cI\u2019ve read the big distributed systems books. This isn\u2019t trying to be one of those. It\u2019s tighter, more focused, and immediately useful.\u201d</p>
<footer>\u2014 Daniel S., CTO at a Series A startup</footer>
</blockquote>
</section>

<section class="product-section">
<h2>Purchase options</h2>
<div class="purchase-options">
<div class="purchase-option">
<h3>PDF + EPUB</h3>
<p class="purchase-price">$24</p>
<p>Both formats, all future updates included. Read on your Kindle, iPad, or laptop.</p>
</div>
<div class="purchase-option">
<h3>Pay what you can</h3>
<p class="purchase-price">$10+</p>
<p>If $24 is too much right now, pay what works for you. No questions, no guilt. I\u2019d rather you read it than not.</p>
</div>
</div>
</section>""",
                'content_uz': """<section class="product-hero">
<h1>Keshlash haqida kichik kitob</h1>
<p class="lead">Keshlash haqida bilgan hamma narsam 90 sahifaga sig\u2018dirilgan. Ishlaydigan shablonlar, ishlamaydigan tuzoqlar va TypeScript\u2019da 24 ta ishlangan misol. Bu saytni boshlagan blog post, to\u2018lashga arziydigan narsaga kengaytirilgan.</p>
</section>

<section class="product-section">
<h2>Mundarija</h2>
<div class="toc">
<ol>
<li><strong>1-bob: TTL\u2019li Map</strong> \u2014 Nima uchun har bir kesh bu yerdan boshlanadi va ko\u2018pchilik siz o\u2018ylaganingizdan ko\u2018proq bu yerda qolishi kerak.</li>
<li><strong>2-bob: Invalidatsiya \u2014 qiyin qism</strong> \u2014 Write-through, write-behind va haqiqatan ham masshtabda ishlaydigan hodisalarga asoslangan yondashuv.</li>
<li><strong>3-bob: Kesh stampedalari</strong> \u2014 Bir vaqtning o\u2018zida yuzta so\u2018rov bo\u2018sh keshga tushganda nima bo\u2018ladi va buni oldini olishning uch usuli.</li>
<li><strong>4-bob: Qatlamli keshlar</strong> \u2014 Tezlik ham, izchillik ham kerak bo\u2018lgan ilovalar uchun L1/L2 shablonlari. Redis va jarayon ichidagi Map\u2019ni qachon ishlatish kerak.</li>
<li><strong>5-bob: Kesh kalitlari \u2014 dizayn qarori</strong> \u2014 Nomlash konvensiyalari, versiyalash strategiyalari va ma\u2019lumotlaringizni buzadigan bitta xato.</li>
<li><strong>6-bob: Kesh samaradorligini o\u2018lchash</strong> \u2014 Hit nisbatlari, kechikish persentillari va keshingiz foyda keltirganidan ko\u2018proq zarar yetkazayotganini qanday bilish mumkin.</li>
<li><strong>7-bob: Edge\u2019da keshlash</strong> \u2014 CDN keshlash, stale-while-revalidate va Cache-Control sarlavhalarining kutilmaganda murakkab dunyosi.</li>
<li><strong>8-bob: Qachon keshlash kerak emas</strong> \u2014 Kesh qo\u2018shish hamma narsani yomonlashtiradigan holatlar. Yetkazishdan oldin ularni aniqlash.</li>
</ol>
</div>
</section>

<section class="product-section">
<h2>Namuna: 3-bob</h2>
<blockquote class="book-excerpt">
<p>Tasavvur qiling, kesh kalitingiz 12:00:00 da tugaydi. 12:00:01 da bir xil resurs uchun 200 ta so\u2018rov keladi. Har biri kesh o\u2018tkazib yuborishni ko\u2018radi. Har biri ma\u2019lumotlar bazasiga murojaat qiladi. Soniyasiga 10 ta so\u2018rovga xizmat qilayotgan ma\u2019lumotlar bazasi endi bir soniyada 200 ta oladi. U sekinlashadi. So\u2018rovlar ko\u2018proq vaqt oladi. Ko\u2018proq so\u2018rovlar ularning orqasida to\u2018planadi. Bu kesh stampedasi va u ko\u2018p muhandislar tushunganidan ko\u2018proq ishlab chiqarish tizimlarini yiqitgan.</p>
<p>Tuzatish aldamchi darajada oddiy: faqat bitta so\u2018rovni o\u2018tkazing. Qolganlari kutadi. Birinchi so\u2018rov keshni to\u2018ldiradi va qolganlari undan o\u2018qiydi. Bu \u201crequest coalescing\u201d yoki \u201csingle-flight\u201d deb ataladi va uni to\u2018g\u2018ri amalga oshirish ushbu bobning mavzusi.</p>
</blockquote>
</section>

<section class="product-section">
<h2>O\u2018quvchilar nima deydi</h2>
<blockquote>
<p>\u201cBu besh yil oldin bo\u2018lishini xohlagan keshlash kitobi. Qisqa, amaliy va men haqiqatan ham ishlab chiqarishga nusxalagan kodga to\u2018la.\u201d</p>
<footer>\u2014 James L., Principal Engineer</footer>
</blockquote>
<blockquote>
<p>\u201cFaqat kesh kalitlari haqidagi 5-bob meni kunlab izlashga to\u2018g\u2018ri keladigan xatodan qutqardi. Har bir tiyinga arziydi.\u201d</p>
<footer>\u2014 Aisha T., Backend Developer</footer>
</blockquote>
<blockquote>
<p>\u201cKatta taqsimlangan tizimlar kitoblarini o\u2018qiganman. Bu ulardan biri bo\u2018lishga urinmayapti. U yanada ixcham, yo\u2018naltirilgan va darhol foydali.\u201d</p>
<footer>\u2014 Daniel S., Series A startap CTO\u2019si</footer>
</blockquote>
</section>

<section class="product-section">
<h2>Sotib olish imkoniyatlari</h2>
<div class="purchase-options">
<div class="purchase-option">
<h3>PDF + EPUB</h3>
<p class="purchase-price">$24</p>
<p>Ikkala format, barcha kelajakdagi yangilanishlar kiritilgan. Kindle, iPad yoki noutbukda o\u2018qing.</p>
</div>
<div class="purchase-option">
<h3>O\u2018zingiz xohlagan narxda</h3>
<p class="purchase-price">$10+</p>
<p>Agar $24 hozir ko\u2018p bo\u2018lsa, o\u2018zingizga mos narxni to\u2018lang. Savolsiz, aybsiz. Men sizning o\u2018qishingizni xohlayman.</p>
</div>
</div>
</section>""",
                'bullets': [
                    ('PDF + EPUB', 'PDF + EPUB'),
                    ('24 worked examples in TypeScript', 'TypeScript\u2019da 24 ta ishlangan misol'),
                    ('Pay-what-you-can option', 'O\u2018zingiz xohlagan narxda to\u2018lash imkoni'),
                ],
            },
        ]
        for pdata in products_data:
            bullets = pdata.pop('bullets')
            prod, _ = Product.objects.update_or_create(name_en=pdata['name_en'], defaults=pdata)
            prod.bullets.all().delete()
            for i, (text_en, text_uz) in enumerate(bullets):
                ProductBullet.objects.create(product=prod, text_en=text_en, text_uz=text_uz, order=i)
        self.stdout.write(f'  Created {len(products_data)} products')

    def seed_newsletter_issues(self):
        issues = [
            {
                'number': 18,
                'date_en': 'April 2026', 'date_uz': '2026 aprel',
                'title_en': 'Caching, an essay; tinyq v1.2; what I read in March.',
                'title_uz': 'Keshlash haqida esse; tinyq v1.2; martda nimani o\u2018qiganim.',
                'content_en': """<h2>What I shipped</h2>
<p>The big one this month: <a href="/writing/notes-on-caching">Notes on caching, in three parts</a>. This started as a section in the book, but it grew legs and became its own essay. It covers the naive Map-with-TTL approach, where it breaks down, and the layered pattern I reach for now. Writing it took three weeks; editing it took two more. That ratio feels about right.</p>
<p>I also pushed <strong>tinyq v1.2</strong>, which adds configurable retry backoff and a small dashboard for inspecting jobs. The dashboard is one HTML file with no dependencies. I\u2019m unreasonably proud of it.</p>

<h2>What I read</h2>
<ul>
<li><strong>\u201cDesigning Data-Intensive Applications\u201d by Martin Kleppmann</strong> \u2014 A re-read, third time now. I pick up something new every time. This round it was the section on linearizability vs. serializability, which finally clicked.</li>
<li><strong>\u201cThe Courage to Be Disliked\u201d by Ichiro Kishimi</strong> \u2014 Not a tech book. A philosophy book disguised as a dialogue. Made me rethink how I handle feedback from strangers on the internet.</li>
<li><strong>Julia Evans\u2019 latest zine on DNS</strong> \u2014 Julia has a gift for making complex things feel approachable. I wish I could draw like her.</li>
</ul>

<h2>One thing I\u2019m thinking about</h2>
<p>I\u2019ve been thinking a lot about the difference between writing for discovery and writing for communication. When I write blog posts, I\u2019m usually discovering what I think as I go. But the reader needs the finished version \u2014 the version where I already know the answer. The gap between those two is where editing lives, and I think most technical writers (myself included) don\u2019t spend enough time there.</p>""",
                'content_uz': """<h2>Nimalarni yetkazdim</h2>
<p>Bu oyning eng kattasi: <a href="/writing/notes-on-caching">Keshlash haqida eslatmalar, uch qismda</a>. Bu kitobdagi bo\u2018lim sifatida boshlangan edi, lekin o\u2018sib, mustaqil essega aylandi. U sodda Map-with-TTL yondashuvini, qayerda buzilishini va men hozir murojaat qiladigan qatlamli shablonni qamrab oladi. Yozish uch hafta davom etdi; tahrir yana ikkita. Bu nisbat to\u2018g\u2018ri tuyuladi.</p>
<p>Shuningdek, <strong>tinyq v1.2</strong> ni chiqardim, u sozlanadigan qayta urinish kechikishi va vazifalarni ko\u2018rish uchun kichik panelni qo\u2018shadi. Panel \u2014 hech qanday bog\u2018lanishlarsiz bitta HTML fayl. Men undan asossiz darajada faxrlanaman.</p>

<h2>Nimalarni o\u2018qidim</h2>
<ul>
<li><strong>\u201cDesigning Data-Intensive Applications\u201d \u2014 Martin Kleppmann</strong> \u2014 Qayta o\u2018qish, uchinchi marta. Har safar yangi narsa topaman. Bu safar linearizability va serializability haqidagi bo\u2018lim edi, nihoyat tushundim.</li>
<li><strong>\u201cThe Courage to Be Disliked\u201d \u2014 Ichiro Kishimi</strong> \u2014 Texnik kitob emas. Muloqot niqobidagi falsafa kitobi. Internetdagi notanishlarning fikr-mulohazalariga munosabatimni qayta ko\u2018rib chiqdim.</li>
<li><strong>Julia Evans\u2019ning DNS haqidagi so\u2018nggi zini</strong> \u2014 Julia murakkab narsalarni tushunarli qilish iste\u2019dodiga ega. Uning kabi rasm chiza olsam degan edim.</li>
</ul>

<h2>O\u2018ylayotgan bir narsa</h2>
<p>Kashf qilish uchun yozish va muloqot uchun yozish orasidagi farq haqida ko\u2018p o\u2018yladim. Blog post yozganimda, odatda yozish jarayonida nima o\u2018ylayotganimni kashf qilaman. Lekin o\u2018quvchiga tayyor versiya kerak \u2014 men allaqachon javobni bilgan versiya. Bu ikki narsa orasidagi bo\u2018shliq \u2014 tahrir yashaydigan joy, va menimcha ko\u2018pchilik texnik yozuvchilar (men ham) u yerda yetarlicha vaqt o\u2018tkazmaydi.</p>""",
            },
            {
                'number': 17,
                'date_en': 'March 2026', 'date_uz': '2026 mart',
                'title_en': 'Why I stopped reaching for Redux; a small Postgres trick.',
                'title_uz': 'Nega Redux\u2019dan voz kechganim; kichik Postgres hiylasi.',
                'content_en': """<h2>What I shipped</h2>
<p>Published <a href="/writing/i-stopped-reaching-for-redux">I stopped reaching for Redux</a>. This one struck a nerve \u2014 it got picked up on Twitter and sparked a surprisingly civil debate about state management in 2026. The TLDR: for most apps, React context + useReducer is enough. For large apps, Zustand. Redux is still fine, but it\u2019s not the default anymore.</p>
<p>On the tinyq side, I\u2019ve been quietly rewriting the persistence layer. The current version uses raw SQLite queries; the new version uses a thin query builder I wrote in about 200 lines. It\u2019s not an ORM \u2014 it\u2019s just enough abstraction to stop me from writing the same WHERE clause twelve times.</p>

<h2>What I read</h2>
<ul>
<li><strong>\u201cA Philosophy of Software Design\u201d by John Ousterhout</strong> \u2014 Finally read it. The chapter on \u201cdeep modules\u201d alone is worth the cover price. Made me rethink how I structure my libraries.</li>
<li><strong>Postgres docs: pg_stat_statements</strong> \u2014 I keep coming back to these. If you run Postgres and you\u2019re not using pg_stat_statements, you\u2019re flying blind.</li>
<li><strong>A thread by @brandur on idempotency keys</strong> \u2014 Short, precise, and changed how I think about payment APIs.</li>
</ul>

<h2>One thing I\u2019m thinking about</h2>
<p>I had a conversation with a friend who runs a small SaaS about the \u201cpremium mediocre\u201d trap \u2014 the tendency to build features that are impressive in demos but don\u2019t move the needle for actual users. His product has 47 features and 3 that matter. He knows which 3. He can\u2019t bring himself to kill the other 44. I think about this every time I\u2019m tempted to add a feature to tinyq.</p>""",
                'content_uz': """<h2>Nimalarni yetkazdim</h2>
<p><a href="/writing/i-stopped-reaching-for-redux">Men Redux\u2019ga qo\u2018l urishni to\u2018xtatdim</a> nashr qildim. Bu asabga tegdi \u2014 Twitter\u2019da tarqaldi va 2026-yilda holat boshqaruvi haqida kutilmaganda madaniy munozarani boshladi. Qisqasi: ko\u2018pchilik ilovalar uchun React context + useReducer yetarli. Katta ilovalar uchun Zustand. Redux hali ham yaxshi, lekin u endi standart emas.</p>
<p>tinyq tomonida, men jimgina saqlash qatlamini qayta yozyapman. Hozirgi versiya to\u2018g\u2018ridan-to\u2018g\u2018ri SQLite so\u2018rovlarini ishlatadi; yangi versiya men taxminan 200 qatorda yozgan yengil so\u2018rov quruvchisini ishlatadi. Bu ORM emas \u2014 shunchaki bir xil WHERE bandini o\u2018n ikki marta yozishni to\u2018xtatish uchun yetarli abstraktsiya.</p>

<h2>Nimalarni o\u2018qidim</h2>
<ul>
<li><strong>\u201cA Philosophy of Software Design\u201d \u2014 John Ousterhout</strong> \u2014 Nihoyat o\u2018qidim. Faqat \u201cchuqur modullar\u201d haqidagi bob muqovasi narxiga arziydi. Kutubxonalarimni qanday tuzishim haqida qayta o\u2018yladim.</li>
<li><strong>Postgres hujjatlari: pg_stat_statements</strong> \u2014 Doimo qaytib kelaman. Agar Postgres ishlatib, pg_stat_statements ishlatmayotgan bo\u2018lsangiz, ko\u2018r-ko\u2018rona uchyapsiz.</li>
<li><strong>@brandur\u2019ning idempotency kalitlari haqidagi mavzusi</strong> \u2014 Qisqa, aniq va to\u2018lov API\u2019lari haqidagi fikrimni o\u2018zgartirdi.</li>
</ul>

<h2>O\u2018ylayotgan bir narsa</h2>
<p>Kichik SaaS boshqaradigan do\u2018stim bilan \u201cpremium o\u2018rtacha\u201d tuzoq haqida suhbatlashdim \u2014 demolarda ta\u2019sirli ko\u2018rinadigan, lekin haqiqiy foydalanuvchilar uchun ahamiyatsiz xususiyatlar yaratish tendensiyasi. Uning mahsulotida 47 ta xususiyat bor va muhimi 3 tasi. U qaysi 3 tasini biladi. Qolgan 44 tasini o\u2018chirishga ko\u2018ngli to\u2018lmaydi. Men tinyq\u2019ga xususiyat qo\u2018shishga vasvasaga tushganda doimo bu haqda o\u2018ylayman.</p>""",
            },
            {
                'number': 16,
                'date_en': 'February 2026', 'date_uz': '2026 fevral',
                'title_en': 'The cost of a yes; three small tools I am using.',
                'title_uz': '"Ha"ning narxi; men ishlatayotgan uch kichik vosita.',
                'content_en': """<h2>What I shipped</h2>
<p>Published <a href="/writing/the-cost-of-a-yes">The cost of a yes</a> \u2014 a short essay about saying yes to too many things and the compound interest of overcommitment. I wrote it in a single sitting after turning down three consulting requests in one week. It\u2019s not technical, but it\u2019s the most-shared thing I\u2019ve written this year.</p>
<p>Also quietly released <strong>paper-cuts v0.3</strong>, which now supports Postgres 16 and handles partitioned tables correctly. Nobody asked for partitioned table support; I just needed it for a client project and figured I\u2019d upstream it.</p>

<h2>What I read</h2>
<ul>
<li><strong>\u201cFour Thousand Weeks\u201d by Oliver Burkeman</strong> \u2014 A book about time management that is actually a book about mortality. Deeply uncomfortable in the best way.</li>
<li><strong>The SQLite documentation on WAL mode</strong> \u2014 I re-read this every few months. It\u2019s some of the best technical documentation ever written. Clear, honest about trade-offs, and short.</li>
<li><strong>A blog post by Xe Iaso on NixOS</strong> \u2014 I\u2019m not switching to NixOS, but I admire the thinking. Declarative infrastructure for your laptop is a wild idea that might actually be right.</li>
</ul>

<h2>One thing I\u2019m thinking about</h2>
<p>Three small tools I\u2019ve started using this month that I think are underrated: <strong>direnv</strong> (per-directory environment variables \u2014 I don\u2019t know how I lived without it), <strong>just</strong> (a command runner that replaces Make for 90% of what I use Make for), and <strong>mprocs</strong> (run multiple processes in one terminal with a TUI). None of these are new, but discovering them at the right time made my daily workflow noticeably better.</p>""",
                'content_uz': """<h2>Nimalarni yetkazdim</h2>
<p><a href="/writing/the-cost-of-a-yes">"Ha"ning narxi</a> nashr qildim \u2014 juda ko\u2018p narsaga ha deyish va haddan tashqari majburiyat olishning murakkab foizi haqida qisqa esse. Bir haftada uchta konsalting so\u2018rovini rad qilgandan keyin bir o\u2018tirishda yozdim. Texnik emas, lekin bu yil yozganlarimning eng ko\u2018p ulashilgani.</p>
<p>Shuningdek, jimgina <strong>paper-cuts v0.3</strong> ni chiqardim, u endi Postgres 16 ni qo\u2018llab-quvvatlaydi va bo\u2018lingan jadvallarni to\u2018g\u2018ri ishlaydi. Hech kim bo\u2018lingan jadval qo\u2018llab-quvvatlashini so\u2018ramagan edi; shunchaki mijoz loyihasi uchun kerak edi va upstream qilishga qaror qildim.</p>

<h2>Nimalarni o\u2018qidim</h2>
<ul>
<li><strong>\u201cFour Thousand Weeks\u201d \u2014 Oliver Burkeman</strong> \u2014 Aslida o\u2018lim haqidagi vaqtni boshqarish kitobi. Eng yaxshi ma\u2019noda chuqur noqulay.</li>
<li><strong>SQLite WAL rejimi haqidagi hujjatlar</strong> \u2014 Men buni har bir necha oyda qayta o\u2018qiyman. Bu hozirgacha yozilgan eng yaxshi texnik hujjatlardan biri. Aniq, savdo-sotiq haqida halol va qisqa.</li>
<li><strong>Xe Iaso\u2019ning NixOS haqidagi blog posti</strong> \u2014 Men NixOS\u2019ga o\u2018tmayman, lekin fikrlash tarziga qoyil qolaman. Noutbukingiz uchun deklarativ infratuzilma \u2014 to\u2018g\u2018ri bo\u2018lishi mumkin bo\u2018lgan g\u2018alati fikr.</li>
</ul>

<h2>O\u2018ylayotgan bir narsa</h2>
<p>Bu oy ishlatishni boshlagan uchta kichik vosita, menimcha, kam baholanadi: <strong>direnv</strong> (har bir katalog uchun muhit o\u2018zgaruvchilari \u2014 usiz qanday yashaganimni bilmayman), <strong>just</strong> (Make\u2019ni 90% ishlatishim uchun almashtiradigan buyruq ishga tushiruvchi), va <strong>mprocs</strong> (bitta terminalda TUI bilan bir nechta jarayonni ishga tushirish). Bularning hech biri yangi emas, lekin to\u2018g\u2018ri vaqtda kashf qilish kundalik ish jarayonimni sezilarli darajada yaxshiladi.</p>""",
            },
            {
                'number': 15,
                'date_en': 'January 2026', 'date_uz': '2026 yanvar',
                'title_en': "Postgres as everything; books I'm starting the year on.",
                'title_uz': 'Postgres \u2014 hamma narsa o\u2018rnida; yilni boshlayotgan kitoblarim.',
                'content_en': """<h2>What I shipped</h2>
<p>Published <a href="/writing/postgres-as-everything">Postgres as everything</a> \u2014 a long post about using Postgres as a job queue (SKIP LOCKED), a search engine (tsvector), a pub/sub system (LISTEN/NOTIFY), and a blob store (large objects). The verdict: it\u2019s surprisingly good at all of these, and if you\u2019re already running Postgres, you should try them before reaching for a dedicated tool.</p>
<p>I also shipped a small update to <strong>colormath</strong> \u2014 added OKLCH-to-Display P3 conversion and fixed an edge case with very dark colors. Nobody noticed, which is exactly how a color library should work.</p>

<h2>What I read</h2>
<ul>
<li><strong>\u201cThe Art of Doing Science and Engineering\u201d by Richard Hamming</strong> \u2014 My book for Q1. Dense, opinionated, and full of sentences that make you put the book down and stare at the wall. Hamming was thinking about AI in the 1990s, and his predictions are eerily on point.</li>
<li><strong>\u201cStaff Engineer\u201d by Will Larson</strong> \u2014 A re-read before a mentoring session. Still the best book on what it means to be a senior-plus engineer. The section on \u201cbeing glue\u201d resonates every time.</li>
<li><strong>Postgres release notes for v17</strong> \u2014 The incremental sort improvements and the new MERGE syntax are the highlights. Postgres keeps getting better without getting bloated. A rare thing.</li>
</ul>

<h2>One thing I\u2019m thinking about</h2>
<p>New year, new ambitions, same 24 hours. I\u2019m trying something different this year: instead of setting goals, I\u2019m setting constraints. No more than two active side projects. No more than one blog post per month. No consulting on weekends. The theory is that constraints force focus, and focus compounds. Ask me in December if it worked.</p>""",
                'content_uz': """<h2>Nimalarni yetkazdim</h2>
<p><a href="/writing/postgres-as-everything">Postgres \u2014 hamma narsa o\u2018rnida</a> nashr qildim \u2014 Postgres\u2019ni vazifa navbati (SKIP LOCKED), qidiruv tizimi (tsvector), pub/sub tizimi (LISTEN/NOTIFY) va fayl saqlash (large objects) sifatida ishlatish haqida uzoq post. Xulosa: bularning hammasida u kutilmagandan yaxshi va agar allaqachon Postgres ishlatayotgan bo\u2018lsangiz, maxsus vositaga murojaat qilishdan oldin ularni sinab ko\u2018rishingiz kerak.</p>
<p>Shuningdek, <strong>colormath</strong>\u2019ga kichik yangilanish yetkazdim \u2014 OKLCH-to-Display P3 konvertatsiyasini qo\u2018shdim va juda qora ranglar bilan bog\u2018liq chekka holatni tuzatdim. Hech kim sezmadi, bu rang kutubxonasi qanday ishlashi kerak.</p>

<h2>Nimalarni o\u2018qidim</h2>
<ul>
<li><strong>\u201cThe Art of Doing Science and Engineering\u201d \u2014 Richard Hamming</strong> \u2014 Q1 uchun kitobim. Zich, fikrli va kitobni qo\u2018yib, devorga tikilib qolishga majbur qiladigan jumlalarga to\u2018la. Hamming 1990-yillarda AI haqida o\u2018ylagan va uning bashoratlari dahshatli darajada to\u2018g\u2018ri.</li>
<li><strong>\u201cStaff Engineer\u201d \u2014 Will Larson</strong> \u2014 Mentorlik sessiyasidan oldin qayta o\u2018qish. Katta va undan yuqori darajadagi muhandis bo\u2018lish nimani anglatishi haqidagi eng yaxshi kitob. \u201cYelim bo\u2018lish\u201d bo\u2018limi har safar rezonans qiladi.</li>
<li><strong>Postgres v17 reliz eslatmalari</strong> \u2014 Bosqichma-bosqich tartiblash yaxshilanishlari va yangi MERGE sintaksisi asosiy yangiliklar. Postgres shishmasdan yaxshilanib bormoqda. Kam uchraydigan narsa.</li>
</ul>

<h2>O\u2018ylayotgan bir narsa</h2>
<p>Yangi yil, yangi ambitsiyalar, bir xil 24 soat. Bu yil boshqacha narsa sinab ko\u2018ryapman: maqsadlar o\u2018rniga cheklovlar qo\u2018yyapman. Ikkitadan ortiq faol yondosh loyiha emas. Oyiga bittadan ortiq blog post emas. Dam olish kunlari konsalting yo\u2018q. Nazariya shuki, cheklovlar fokusni majbur qiladi va fokus to\u2018planadi. Dekabr\u2019da ishing bitdimi deb so\u2018rang.</p>""",
            },
        ]
        for issue_data in issues:
            num = issue_data.pop('number')
            NewsletterIssue.objects.update_or_create(
                number=num,
                defaults=issue_data
            )
        self.stdout.write(f'  Created {len(issues)} newsletter issues')

    def seed_timeline(self):
        entries = [
            ('2024 \u2014 now', '2024 \u2014 hozir', 'Independent. Consulting + fazliddin.com.', 'Mustaqil. Konsalting + fazliddin.com.', 0),
            ('2021 \u2014 2024', '2021 \u2014 2024', 'Staff engineer at a series-C developer-tools company.', 'Series-C dasturchi vositalari kompaniyasida staff engineer.', 1),
            ('2017 \u2014 2021', '2017 \u2014 2021', 'Engineer at a search company you have heard of.', 'Eshitgan qidiruv kompaniyangizda muhandis.', 2),
            ('2013 \u2014 2017', '2013 \u2014 2017', 'Founding engineer at two startups, one of which is still going.', 'Ikki startapda ta\u2019sischi muhandis, ulardan biri hali ham faoliyat yuritmoqda.', 3),
            ('2011 \u2014 2013', '2011 \u2014 2013', 'Software engineer at a large bank. Useful, not fun.', 'Yirik bankda dasturchi muhandis. Foydali, lekin qiziq emas.', 4),
        ]
        for period_en, period_uz, desc_en, desc_uz, order in entries:
            TimelineEntry.objects.update_or_create(
                period_en=period_en,
                defaults={'period_uz': period_uz, 'description_en': desc_en, 'description_uz': desc_uz, 'order': order}
            )
        self.stdout.write(f'  Created {len(entries)} timeline entries')
