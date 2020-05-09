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

  chatSocket.onopen = function(e) {
    chatSocket.send(JSON.stringify({
      'player': player,
      'command': 'add_player'
    }))}

  function parseInput(message) {
    const regex = new RegExp('/w[ ][A-Za-z_]* ')

    const splitReceiver = regex.exec(message) ? regex.exec(message)[0] : '' // /w example_mame
    const receiver = splitReceiver ? splitReceiver.split(' ')[1] : room // example_name
    // const newMessage = message.replace(splitReceiver + ' ', '')
    return receiver
  }

  chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    //Incoming Message
    if (data.receiver === room || data.receiver === player || data.player === player){
        document.querySelector('#chat-log').value += ( data.player + ': ' + data.message + '\n');
    }

    //kick loser if round over
    if(data.round_over === true) {
      if(data.current_loser === player) {
        window.location.pathname = '/home/'
      } else {
        $(`.${data.current_loser}`).remove()
        $('.vote-button').removeClass('disabled')
      }
    }

    //Player has joined, create new element
    if(data.is_new_player && data.player != player) {
      var survivorDiv = $('.survivor-wrapper').clone()[0]
      $(survivorDiv).find('.vote-button').attr('data-survivor', data.player)
      $(survivorDiv).find('.vote-selection').text(data.player)
      $('.survivors-list').append(survivorDiv)
    }
  };

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
      receiver = room
      $('#chat-message-input').removeClass('private-message')
      }
  };

  $('.vote-button').click(e => {
    $('.vote-button').addClass('disabled');
    chatSocket.send(JSON.stringify({
        'player': player,
        'votee' : e.target.getAttribute('data-survivor'),
        'command': 'vote'
    }))});

}
