$(document).ready(function(){
  var games, exercises
    , editing = false

  $.when(
    $.get('/static/js/templates/braingames.handlebars'),
    $.getJSON('/api/brain-games'),
    $.get('/static/js/templates/brain-exercises.handlebars'),
    $.getJSON('/api/brain-exercises')
  ).done(function(tmpl1, gamesData, tmpl2, exerciseData){
    games = tmpl1[0]
    exercises = tmpl2[0]

    renderTemplates(
      exercises, 
      exerciseData[0]['data'], 
      'exercises'
    )

    renderTemplates(
      games, 
      gamesData[0]['data'], 
      'games'
    )
  })

  $.getJSON('/api/brain-games',function(data){
    $('#create .game').autocomplete({
      source: _.map(data['data'],function(d){
        return {"label": d['name'], "value": d['id']}
      })
    })
  })

  $('#brain_nav li').on('click', function(ev){
    var $this = $(ev.target)
      , active = $('.active')
      , attr = $this.attr('id')

    $('ul .border').removeClass('border')
    $this.addClass('border')

    active.hide()
    active.removeClass('active')
    $('.'+attr).addClass('active')
    $('.'+attr).show()
  })

  $('#brain_training_container').on('click', 'td:not(.remove)', function(ev){
    $this = $(ev.target)
      , currVal = $this.html()
      , editor = '<input id="editor" type="text" value="' + currVal + '"/>'
    
      setText()
      $this.empty().append(editor)
      $('#editor').focus()
  })

  $('.remove').on('click', function(ev){
    var removalConfirmed = confirm('Are you sure you want to remove this game?')
      , $this = $(ev.target)
      , rowId = $this.parent().attr('class')
      , key = $this.attr('class').split(' ')[0]
      , value = $this.html()

    if (removalConfirmed){
      $.ajax({      
        url: '/api/brain-games?game_id=' + rowId,
        type: 'DELETE',
        success: function(){
          alert('success')
          $this.parent().remove()
        },
        error: function(){
          alert('error')
        }
      })
    }
  })

  $('body').on('keypress', function(ev){
    var editor, key, value, rowId, data

    if (ev.keyCode == 13){
      ev.preventDefault()
      editor = $('#editor')
      rowId = editor.parent().parent().attr('class')
      key = editor.parent().attr('class').split(' ')[0]
      value = editor.val()

      data = {
        game_id: rowId,
        key: key,
        value: value
      }

      $.ajax({      
        url: '/api/brain-games',
        type: 'PUT',
        data: data,
        error: function(){
          alert('error')
        }
      })

      setText()
    }
  });

  $("#create input[type='submit']").on('click', function(ev){
    ev.preventDefault()
    var el = $('#create')
      , game_id = el.find('.game').val()
      , score = el.find('.score').val()
      , data;

    data = {
      'game_id' : game_id,
      'score'   : score,
    }

    $.ajax({
      url: '/api/brain-exercises',
      type: 'POST',
      data: data,
      success: function(){
        alert('success')
      },
      error: function(){
        alert('error')
      }
    })  
  })
})

function renderTemplates(template, data, type){
  var source   = $(template).html()
    , tmpl     = Handlebars.compile(source)
    , tmplData = {}
    , html;

    tmplData[type] = data
    html           = tmpl(tmplData);

  $('#brain_training_container').append(html)
}

function setText(){
  var editor = $('#editor')
    , editorVal = editor.val()
  
  editor.parent().html(editorVal)  
}
