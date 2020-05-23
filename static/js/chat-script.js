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



  function youAreThirdPlaceRender(data) {
    survivor_names.forEach(survivor => {
      const survivorDiv = $(`.survivor-wrapper[data-survivor=${survivor}]`)
      if(data.current_losers.includes(survivor)) {
        survivorDiv.find('.survivor-pill').addClass('voted-out')
        $(survivorDiv).find('.vote-count').text('Voting...')
      } else {
        survivorDiv.find('.vote-button').removeClass('disabled')
      }
    })
  }


  function youAreInFinalRoundRender(data) {
     survivor_names.forEach(survivor => {
      const survivorDiv = $(`.survivor-wrapper[data-survivor=${survivor}]`)
      if(data.current_losers.includes(survivor)) {
        survivorDiv.find('.survivor-pill').addClass('voted-out')
        $(survivorDiv).find('.vote-count').text('Voting...')
      }
    })
  }



  function parseInput(message) {
    const regex = new RegExp('/w[ ][A-Za-z_]* ')

    const splitReceiver = regex.exec(message) ? regex.exec(message)[0] : '' // /w example_mame
    const whispered = splitReceiver ? splitReceiver.split(' ')[1] : room // example_name
    // const newMessage = message.replace(splitReceiver + ' ', '')
    return whispered
  }

  function renderMessageSelectDropdown(message) {
    const regex = new RegExp(
      message.replace(/[-[\]{}()*+?.,\\/^$|#\s]/g, "\\$&"),
      "i"
    );
    var resultHTML = ''

    const result = survivor_names.filter(name => regex.test(name))
    const isLastOption = Object.keys(result).length == 1
    if(isLastOption) {
      $('.tab-select').show()
    } 
    else {
      $('.tab-select').hide()
    }
    for (var key in result) {
      const survivor = result[key]
      const selected = isLastOption ? 'selected' : ''
      resultHTML += `<div class='message-survivor-option ${selected}' data-survivor=${survivor}>${survivor}</div>`
    }
    $('.survivor-name-dropdown').html(resultHTML)
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
      if(data.current_losers.includes(player)) {
        window.location.pathname = '/home/'
      } else {
        data.current_losers.forEach(loser => { //remove all losers
          $(`.survivor-wrapper[data-survivor=${loser}]`).remove()
        })
        $('.vote-button').removeClass('disabled')
        $('.survivor-pill').removeClass('voted-out')
        survivor_names.forEach((s, index) => {
          const survivorDiv = $(`.survivor-wrapper[data-survivor=${s}]`)
          var text = data[s] || 0
          var voteLabel = data[s] === 1 ? 'Vote' : 'Votes'
          // $(`.vote-count.${s}`).text(`${text} ${voteLabel}`)
          $(survivorDiv).find('.vote-count').text(`${text} ${voteLabel}`)
        })
      }
    }

    //Generate final round state.
    if(data.final_round === true) {
      $('.survivor-pill').removeClass('voted-out')
      if(data.current_losers.includes(player)) {
        youAreThirdPlaceRender(data)
      } else {
        youAreInFinalRoundRender(data)
      }
    }

    if(data.game_over === true) {
      const winner = survivor_names.filter(x => !data.current_losers.includes(x))[0]
      const winnerDiv = $(`.survivor-wrapper[data-survivor=${winner}]`)
      $(winnerDiv).addClass('winner')
      if(winner === player) {
        $(winnerDiv).find('vote-count').text('You Won!')
      } else {
         $(winnerDiv).find('vote-count').text('Winner!')
      }
    }

    //Player has joined, create new element
    if(data.is_new_player && data.player != player && !survivor_names.includes(data.player)) {
      var survivorDiv = $('.survivor-wrapper').clone()[0]
      $(survivorDiv).attr('data-survivor', data.player)
      $(survivorDiv).find('.vote-selection').text(`${data.player}`)
      $(survivorDiv).find('.vote-button').attr('data-survivor', data.player)
      $('.survivors-list').append(survivorDiv)
      survivor_names.push(data.player)
      if(survivor_names.length >= 2) {
        $('.vote-button').removeClass('disabled')
      }
    }
  };

  chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
  };

  $('#chat-message-input').bind('keydown', e => {
   const messageInputDom = document.querySelector('#chat-message-input');
   if (e.which === 9) { //tab
      e.preventDefault();
      if($('.message-survivor-option.selected').length) {
        messageInputDom.value = "/w " + $('.message-survivor-option.selected').attr('data-survivor')
      }
    }
  })


  $('#chat-message-input').bind('keyup', e => {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    const whispered = parseInput(message)
    if(message.includes('/w ')) {
      const rawMessage = message.replace('/w ', '')
      renderMessageSelectDropdown(rawMessage)
      $('.dropdown-wrapper').show()
    } else {
      $('.dropdown-wrapper').hide()
    }
    if(survivor_names.includes(whispered)) {
      receiver = whispered
      $('#chat-message-input').addClass('private-message')
      messageInputDom.value = ''
      messageInputDom.placeholder = `Whisper ${receiver}...`
    }
    if (e.which === 13) {  // enter, return 
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
  });

  $('.vote-button').live('click', e => {
    $('.vote-button').addClass('disabled');
    var selectedSurvivor = e.target.getAttribute('data-survivor')
    $(`.survivor-wrapper[data-survivor=${selectedSurvivor}]`).find('.survivor-pill').addClass('voted-out')
    chatSocket.send(JSON.stringify({
        'player': player,
        'votee' : e.target.getAttribute('data-survivor') ,
        'command': 'vote'
    }))});

  $('.survivor-name-dropdown').click(e => {
    const survivor = $(e.target).attr('data-survivor')
    $('#chat-message-input').val(`/w ${survivor}`)
    $('#chat-message-input').focus();
  })

}
