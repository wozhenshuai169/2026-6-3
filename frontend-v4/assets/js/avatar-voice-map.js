(function (global) {
  'use strict';

  var root = global.Aurelian = global.Aurelian || {};
  var voices = {
    guide_female: {
      label: '温柔女声',
      imageUrl: '/assets/images/digital-guide-foreground.png',
      speakingImageUrl: '/assets/images/digital-guide-foreground-open.png',
      role: 'head-only',
      configRole: 'tongtong',
      alt: '温柔女声数字讲解员'
    },
    xiaomei: {
      label: '活力女声',
      imageUrl: '/assets/images/digital-avatar-b.png',
      speakingImageUrl: '/assets/images/digital-avatar-b-open.png',
      role: 'yunchuan',
      configRole: 'yunchuan',
      alt: '活力女声数字讲解员'
    },
    guide_male: {
      label: '沉稳男声',
      imageUrl: '/assets/images/digital-avatar-a.png',
      speakingImageUrl: '/assets/images/digital-avatar-a-open.png',
      role: 'xiaoyun',
      configRole: 'xiaoyun',
      alt: '沉稳男声数字讲解员'
    },
    xiaowei: {
      label: '专业男声',
      imageUrl: '/assets/images/digital-avatar-professional-male.png',
      speakingImageUrl: '/assets/images/digital-avatar-professional-male-open.png',
      role: 'professional-male',
      configRole: 'tongtong',
      alt: '专业男声数字讲解员'
    }
  };

  function get(voice) {
    return voices[voice] || voices.guide_female;
  }

  function isCustomImage(imageUrl) {
    return typeof imageUrl === 'string' && imageUrl.indexOf('/uploads/avatar/') === 0;
  }

  function apply(voice, image, frame, options) {
    if (!image) return get(voice);
    var character = get(voice);
    var customImageUrl = options && isCustomImage(options.customImageUrl) ? options.customImageUrl : '';
    var closedImageUrl = customImageUrl || character.imageUrl;
    image.src = closedImageUrl;
    image.setAttribute('data-closed-src', closedImageUrl);
    image.alt = customImageUrl ? '自定义数字讲解员形象' : character.alt;
    if (!customImageUrl && character.speakingImageUrl) {
      image.setAttribute('data-speaking-src', character.speakingImageUrl);
      var preload = new Image();
      preload.src = new URL(character.speakingImageUrl, document.baseURI).href;
    } else {
      image.removeAttribute('data-speaking-src');
    }
    if (frame) frame.setAttribute('data-avatar-role', customImageUrl ? (options.customRole || character.role) : character.role);
    return character;
  }

  root.avatarVoices = {
    voices: voices,
    get: get,
    apply: apply,
    isCustomImage: isCustomImage
  };
})(window);
