// ── RAFEEQ TRANSLATION ENGINE ─────────────────────────────────
// Usage: include this script, add data-i18n="key" to elements

const TRANSLATIONS = {
    en: {
        // NAVBAR
        nav_listings: 'Listings',
        nav_map: 'Map',
        nav_login: 'Login',
        nav_signup: 'Sign Up',
        nav_messages: '💬 Messages',
        nav_post: '+ Post Listing',
        nav_logout: 'Logout',

        // HERO
        hero_title: 'Find Your Perfect <span>Home in Amman</span>',
        hero_sub: 'Verified shared and private apartments, built for students in Jordan.',

        // FILTERS
        filter_label: 'Filter:',
        filter_all_genders: 'All Genders',
        filter_males: 'Males Only',
        filter_females: 'Females Only',
        filter_all_types: 'All Types',
        filter_shared: 'Shared',
        filter_private: 'Private',
        filter_all_areas: 'All Areas',
        filter_sort_latest: 'Latest First',
        filter_sort_asc: 'Price: Low to High',
        filter_sort_desc: 'Price: High to Low',
        filter_max_rent: 'Max rent (JD)',
        filter_showing: 'Showing',
        filter_listings: 'listings',

        // CARDS
        per_month: '/month',
        rooms: 'rooms',
        males_only: '👨 Males Only',
        females_only: '👩 Females Only',
        any_gender: '👥 Any Gender',
        type_shared: '🏘 Shared',
        type_private: '🏠 Private',

        // AUTH MODAL
        welcome_back: 'Welcome back',
        create_account: 'Create your account',
        email_placeholder: 'Email address',
        password_placeholder: 'Password',
        btn_login: 'Log In',
        no_account: "Don't have an account?",
        sign_up_link: 'Sign up',
        full_name: 'Full name',
        password_hint: 'Password (min 6 characters)',
        select_gender: 'Select gender',
        gender_male: 'Male',
        gender_female: 'Female',
        phone_optional: 'Phone number (optional)',
        btn_create: 'Create Account',
        have_account: 'Already have an account?',
        log_in_link: 'Log in',

        // POST LISTING
        post_title: 'Post a Listing',
        pl_title: 'Title *',
        pl_title_ph: 'e.g. Room in Sweifieh Apartment',
        pl_desc: 'Description',
        pl_desc_ph: 'Describe your apartment...',
        pl_type: 'Type *',
        pl_select_type: 'Select type',
        pl_gender_pref: 'Gender Preference *',
        pl_select_gender: 'Select preference',
        pl_males_only: 'Males Only',
        pl_females_only: 'Females Only',
        pl_any: 'Any Gender',
        pl_rent: 'Monthly Rent (JD) *',
        pl_rent_ph: 'e.g. 150',
        pl_rooms: 'Number of Rooms',
        pl_rooms_ph: 'e.g. 3',
        pl_area: 'Area *',
        pl_select_area: 'Select area',
        pl_pin: '📍 Pin Your Apartment Location',
        pl_pin_hint: 'Click the map to drop a pin on your exact location',
        pl_pinned: 'Location pinned!',
        pl_tags: 'Lifestyle Tags',
        pl_id_label: '🪪 National ID Photo *',
        pl_id_hint: 'Click to upload your National ID photo',
        pl_id_privacy: 'Required for verification. Your ID will only be seen by Rafeeq admins and never shared publicly.',
        pl_submit: 'Submit Listing for Review',
        pl_success: 'Listing submitted! It will go live after admin review.',

        // LISTING PAGE
        back: '← Back to listings',
        monthly_rent: 'Monthly Rent',
        stat_rooms: 'Rooms',
        stat_type: 'Type',
        stat_area: 'Area',
        about: 'About this listing',
        lifestyle: 'Lifestyle & Preferences',
        listed_by: 'Listed by',
        listing_owner: 'Listing owner',
        contact_owner: '💬 Contact Owner',
        login_to_contact: 'You need to be logged in to contact the owner.',
        btn_login_now: 'Log In',
        btn_signup_now: 'Sign Up',
        report: 'Report this listing',

        // MAP PAGE
        map_filter_label: 'Filter:',
        map_results: 'listings',

        // ADMIN LOGIN
        admin_title: 'Admin Login',
        admin_subtitle: 'Rafeeq Admin Panel',
        admin_btn: 'Sign In',

        // GENERAL
        loading: 'Loading...',
        no_listings: 'No listings found. Try adjusting your filters.',
        own_listing: 'This is your own listing.',
    },

    ar: {
        // NAVBAR
        nav_listings: 'الإعلانات',
        nav_map: 'الخريطة',
        nav_login: 'تسجيل الدخول',
        nav_signup: 'إنشاء حساب',
        nav_messages: '💬 الرسائل',
        nav_post: '+ نشر إعلان',
        nav_logout: 'تسجيل الخروج',

        // HERO
        hero_title: 'ابحث عن <span>منزلك المثالي في عمّان</span>',
        hero_sub: 'شقق مشتركة وخاصة موثوقة، مصممة خصيصاً لطلاب الجامعات في الأردن.',

        // FILTERS
        filter_label: 'تصفية:',
        filter_all_genders: 'جميع الجنسين',
        filter_males: 'ذكور فقط',
        filter_females: 'إناث فقط',
        filter_all_types: 'جميع الأنواع',
        filter_shared: 'مشترك',
        filter_private: 'خاص',
        filter_all_areas: 'جميع المناطق',
        filter_sort_latest: 'الأحدث أولاً',
        filter_sort_asc: 'السعر: من الأقل للأعلى',
        filter_sort_desc: 'السعر: من الأعلى للأقل',
        filter_max_rent: 'أقصى إيجار (دينار)',
        filter_showing: 'عرض',
        filter_listings: 'إعلان',

        // CARDS
        per_month: '/شهر',
        rooms: 'غرف',
        males_only: '👨 ذكور فقط',
        females_only: '👩 إناث فقط',
        any_gender: '👥 الجنسين',
        type_shared: '🏘 مشترك',
        type_private: '🏠 خاص',

        // AUTH MODAL
        welcome_back: 'مرحباً بعودتك',
        create_account: 'إنشاء حسابك',
        email_placeholder: 'البريد الإلكتروني',
        password_placeholder: 'كلمة المرور',
        btn_login: 'تسجيل الدخول',
        no_account: 'ليس لديك حساب؟',
        sign_up_link: 'إنشاء حساب',
        full_name: 'الاسم الكامل',
        password_hint: 'كلمة المرور (6 أحرف على الأقل)',
        select_gender: 'اختر الجنس',
        gender_male: 'ذكر',
        gender_female: 'أنثى',
        phone_optional: 'رقم الهاتف (اختياري)',
        btn_create: 'إنشاء الحساب',
        have_account: 'لديك حساب بالفعل؟',
        log_in_link: 'تسجيل الدخول',

        // POST LISTING
        post_title: 'نشر إعلان',
        pl_title: 'العنوان *',
        pl_title_ph: 'مثال: غرفة في شقة السويفية',
        pl_desc: 'الوصف',
        pl_desc_ph: 'صف شقتك...',
        pl_type: 'النوع *',
        pl_select_type: 'اختر النوع',
        pl_gender_pref: 'تفضيل الجنس *',
        pl_select_gender: 'اختر التفضيل',
        pl_males_only: 'ذكور فقط',
        pl_females_only: 'إناث فقط',
        pl_any: 'الجنسين',
        pl_rent: 'الإيجار الشهري (دينار) *',
        pl_rent_ph: 'مثال: 150',
        pl_rooms: 'عدد الغرف',
        pl_rooms_ph: 'مثال: 3',
        pl_area: 'المنطقة *',
        pl_select_area: 'اختر المنطقة',
        pl_pin: '📍 حدد موقع شقتك على الخريطة',
        pl_pin_hint: 'انقر على الخريطة لتحديد الموقع',
        pl_pinned: 'تم تحديد الموقع!',
        pl_tags: 'نمط الحياة',
        pl_id_label: '🪪 صورة الهوية الوطنية *',
        pl_id_hint: 'انقر لرفع صورة هويتك الوطنية',
        pl_id_privacy: 'مطلوب للتحقق. لن يرى هويتك إلا مشرفو رفيق ولن تُشارك علناً.',
        pl_submit: 'إرسال الإعلان للمراجعة',
        pl_success: 'تم إرسال إعلانك! سيُنشر بعد مراجعة المشرف.',

        // LISTING PAGE
        back: '→ العودة للإعلانات',
        monthly_rent: 'الإيجار الشهري',
        stat_rooms: 'الغرف',
        stat_type: 'النوع',
        stat_area: 'المنطقة',
        about: 'عن هذا الإعلان',
        lifestyle: 'نمط الحياة والتفضيلات',
        listed_by: 'نشر بواسطة',
        listing_owner: 'صاحب الإعلان',
        contact_owner: '💬 تواصل مع المالك',
        login_to_contact: 'يجب تسجيل الدخول للتواصل مع المالك.',
        btn_login_now: 'تسجيل الدخول',
        btn_signup_now: 'إنشاء حساب',
        report: 'الإبلاغ عن هذا الإعلان',

        // MAP PAGE
        map_filter_label: 'تصفية:',
        map_results: 'إعلان',

        // ADMIN LOGIN
        admin_title: 'دخول المشرف',
        admin_subtitle: 'لوحة تحكم رفيق',
        admin_btn: 'دخول',

        // GENERAL
        loading: 'جاري التحميل...',
        no_listings: 'لا توجد إعلانات. جرّب تغيير الفلاتر.',
        own_listing: 'هذا إعلانك الخاص.',
    }
};

// ── ENGINE ────────────────────────────────────────────────────

function getLang() {
    return localStorage.getItem('rafeeq_lang') || 'en';
}

function setLang(lang) {
    localStorage.setItem('rafeeq_lang', lang);
    applyLang();
}

function t(key) {
    const lang = getLang();
    return TRANSLATIONS[lang][key] || TRANSLATIONS['en'][key] || key;
}

function applyLang() {
    const lang = getLang();
    const isAr = lang === 'ar';

    // RTL / LTR
    document.documentElement.setAttribute('dir', isAr ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', lang);

    // Translate all data-i18n elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = t(key);
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            el.placeholder = val;
        } else if (el.tagName === 'OPTION') {
            el.textContent = val;
        } else if (val.includes('<span>')) {
            el.innerHTML = val;
        } else {
            el.textContent = val;
        }
    });

    // Update toggle button appearance
    document.querySelectorAll('.lang-toggle').forEach(btn => {
        btn.innerHTML = isAr
            ? '<span style="font-weight:800;color:var(--accent,#2d6a4f);">عربي</span> | <span style="color:#aaa;">EN</span>'
            : '<span style="font-weight:800;color:var(--accent,#2d6a4f);">EN</span> | <span style="color:#aaa;">عربي</span>';
    });
}

function toggleLang() {
    setLang(getLang() === 'en' ? 'ar' : 'en');
}

// Auto-apply on load
document.addEventListener('DOMContentLoaded', applyLang);