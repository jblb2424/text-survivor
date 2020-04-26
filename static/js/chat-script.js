window.initChat = (room, player) => {
  function parseInput(message) {
    const regex = new RegExp('/w[ ][A-Za-z_]*')

    const splitReceiver = regex.exec(message) ? regex.exec(message)[0] : '' // /w example_mame
    const receiver = splitReceiver ? splitReceiver.split(' ')[1] : room // example_name
    const newMessage = message.replace(splitReceiver + ' ', '')
    return [receiver, newMessage]
  }

  const roomName = JSON.parse(document.getElementById('room-name').textContent);
  //My wonderful websockers
  const chatSocket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/chat/'
    + roomName
    + '/'
  );
  chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.receiver == room || data.receiver == player || data.player == player){
        document.querySelector('#chat-log').value += ( data.player + ': ' + data.message + '\n');
    }
  };

  chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
  };

  document.querySelector('#chat-message-input').focus();
  document.querySelector('#chat-message-input').onkeyup = function(e) {
    if (e.keyCode === 13) {  // enter, return
        document.querySelector('#chat-message-submit').click();
    }
  };

  document.querySelector('.vote-selection').onclick = function(e) {
    chatSocket.send(JSON.stringify({
        'player': player,
        'votee' : e.target.id,
        'command': 'vote'
    }));
  }


  document.querySelector('#chat-message-submit').onclick = function(e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    const parsedInput = parseInput(message)
    const receiver = parsedInput[0]
    const parsedMessage = parsedInput[1]
    chatSocket.send(JSON.stringify({
        'message': parsedMessage,
        'command': 'chat_message',
        'player': player,
        'receiver' : receiver
    }));
    messageInputDom.value = '';
  };
}
