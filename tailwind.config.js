module.exports = {
  content: ['./frontend-v4/**/*.html', './frontend-v4/assets/js/**/*.js'],
  theme: {
    extend: {
      colors: {
        background: '#F5F7F6', surface: '#FFFFFF', primary: '#153F35', secondary: '#C96F3B',
        'on-surface': '#17211E', 'on-surface-variant': '#68736F', outline: '#DCE3DF',
        'surface-container-low': '#F0F4F2', 'surface-variant': '#E7ECE9', success: '#2F9E6F', error: '#C84040'
      },
      fontFamily: {
        'body-md': ['Inter', 'PingFang SC', 'Microsoft YaHei', 'system-ui', 'sans-serif'],
        'headline-md': ['STSong', 'SimSun', 'serif'],
        'label-sm': ['Inter', 'PingFang SC', 'Microsoft YaHei', 'sans-serif']
      },
      spacing: { xs:'4px', sm:'8px', md:'16px', lg:'24px', xl:'32px', '2xl':'48px' }
    }
  },
  plugins: []
};
