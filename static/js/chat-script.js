window.initChat = (room, player, survivors) => {
  var receiver = room
  var survivor_names = []
  for (var key in survivors) {
    survivor_names.push(survivors[key].name)
  }
  //My wonderful websockets
  const chatSocket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/chat/'
    + room
    + '/'
  );
  chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.receiver === room || data.receiver === player || data.player === player){
        document.querySelector('#chat-log').value += ( data.player + ': ' + data.message + '\n');
    }
    if(data.round_over === true) {
      if(data.current_loser === player) {
        window.location.pathname = '/home/'
      } else {
        $(`#${data.current_loser}`).remove()
        $('.vote-selection').removeClass('disabled')
      }
    }
  };

  function parseInput(message) {
    const regex = new RegExp('/w[ ][A-Za-z_]* ')

    const splitReceiver = regex.exec(message) ? regex.exec(message)[0] : '' // /w example_mame
    const receiver = splitReceiver ? splitReceiver.split(' ')[1] : room // example_name
    // const newMessage = message.replace(splitReceiver + ' ', '')
    return receiver
  }

  chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
  };
  document.querySelector('#chat-message-input').focus();
  document.querySelector('#chat-message-input').onkeyup = function(e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    receiver = parseInput(message)
    if(survivor_names.includes(receiver)) {
      $('#chat-message-input').addClass('private-message')
      messageInputDom.value = ''
      messageInputDom.placeholder = `Whisper ${receiver}...`
    }
    if (e.keyCode === 13) {  // enter, return 
      if(message != '') {
        chatSocket.send(JSON.stringify({
            'message': message,
            'command': 'chat_message',
            'player': player,
            'receiver' : receiver
        }));
    }
      messageInputDom.value = '';
      messageInputDom.placeholder = `Send Message...`
      $('#chat-message-input').removeClass('private-message')
      }
  };

  $('.vote-selection').click(e => {
    $('.vote-selection').addClass('disabled');
    chatSocket.send(JSON.stringify({
        'player': player,
        'votee' : e.target.id,
        'command': 'vote'
    }))});

}
