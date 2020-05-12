window.initChat = (room, player, survivors) => {
  var receiver = room
  var survivor_names = []
  for (var key in survivors) {
    survivor_names.push(survivors[key].name)
  }
  if (survivors.length < 2) {
    $('.vote-button').addClass('disabled')
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
    const whispered = splitReceiver ? splitReceiver.split(' ')[1] : room // example_name
    // const newMessage = message.replace(splitReceiver + ' ', '')
    return whispered
  }

  function formatMessage(privateMessage, isOwnPrivateMessage , roomMessage, data) {
    if(privateMessage) {
      return '[ ' + data.player + ' whispers ]: ' 
    }
    if(isOwnPrivateMessage && !roomMessage) {
      return '[ ' + `you whispered ${data.receiver}` +  ' ]: ' 
    }
    return '[ ' + data.player + ' ]: '
  }

  chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    //Incoming Message
    var roomMessage = data.receiver === room
    var privateMessage = data.receiver === player
    var isOwnPrivateMessage = data.player === player
    if (roomMessage || privateMessage || isOwnPrivateMessage && data.message){
        var label = formatMessage(privateMessage, isOwnPrivateMessage, roomMessage, data)
        document.querySelector('#chat-log').value += ( label + data.message + '\n');
    }

    //kick loser(s) if round over
    if(data.round_over === true) {
      if(data.current_loser.includes(player)) {
        window.location.pathname = '/home/'
      } else {
        $(`.survivor-wrapper.${data.current_loser}`).remove()
        $('.vote-button').removeClass('disabled')
        $('.vote-button').removeClass('voted-out')
        survivor_names.forEach((s, index) => {
          var text = data[s] || 0
          var voteLabel = data[s] === 1 ? 'Vote' : 'Votes'
          $(`.vote-count.${s}`).text(`${text} ${voteLabel}`)
        })
      }
    }

    //Player has joined, create new element
    if(data.is_new_player && data.player != player && !survivor_names.includes(data.player)) {
      var survivorDiv = $('.survivor-wrapper').clone()[0]
      $(survivorDiv).find('.vote-button').attr('data-survivor', data.player)
      $(survivorDiv).find('.vote-selection').text(`${data.player}`)
      $('.survivors-list').append(survivorDiv)
      if($('.survivor-wrapper').length >= 2) {
        $('.vote-button').removeClass('disabled')
      }
    }
  };

  chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
  };

  document.querySelector('#chat-message-input').focus();
  document.querySelector('#chat-message-input').onkeyup = function(e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    const whispered = parseInput(message)
    if(survivor_names.includes(whispered)) {
      receiver = whispered
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
      messageInputDom.placeholder = 'Chat to Form Alliances...'
      receiver = room
      $('#chat-message-input').removeClass('private-message')
      }
  };

  $('.vote-button').click(e => {
    $('.vote-button').addClass('disabled');
    var selectedSurvivor = e.target.getAttribute('data-survivor')
    $(`.survivor-pill.${selectedSurvivor}`).addClass('voted-out')
    chatSocket.send(JSON.stringify({
        'player': player,
        'votee' : e.target.getAttribute('data-survivor') ,
        'command': 'vote'
    }))});

}
