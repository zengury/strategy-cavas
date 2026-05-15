const Store = require('electron-store');

const store = new Store({
  schema: {
    apiKey: { type: 'string', default: '' },
    model: { type: 'string', default: 'deepseek-chat' },
  },
});

module.exports = {
  getApiKey: () => store.get('apiKey'),
  setApiKey: (key) => store.set('apiKey', key),
  getModel: () => store.get('model'),
  setModel: (model) => store.set('model', model),
};
