$(document).ready(function(){
  // var template
  // $.get('/static/js/templates/papers.handlebars', function(data){
  //   template = data
  // })
  var editing = false

  $.getJSON('/api/brain',function(data){
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

    active.removeClass('active')
    $this.addClass('active')

    $('#controls').children().hide()
    $('.'+attr).show()
  })

  $('#games td:not(.remove)').on('click', function(ev){
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
        url: '/api/brain?game_id=' + rowId,
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

  // $('.attribute').on('click', function(ev){
  //   var $this = $(ev.target)
  //     , rowId = $this.parent().attr('class')

  //   if (removalConfirmed){
  //     $.ajax({      
  //       url: '/api/brain?game_id=' + rowId,
  //       type: 'DELETE',
  //       success: function(){
  //         alert('success')
  //         $this.parent().remove()
  //       },
  //       error: function(){
  //         alert('error')
  //       }
  //     })
  //   }
  // })

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
        url: '/api/brain',
        type: 'PUT',
        data: data,
        error: function(){
          alert('error')
        }
      })

      setText()        
    }
  })

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
      url: '/api/brain',
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

  // $('.edit').on('click', function(){

  // })

  // $('body').on('click', '.abstract h5, #controls h3', function(ev){
  //   var target = $(ev.target)

  //   if (!(target.next().hasClass('hidden'))){
  //     target.next().addClass('hidden')
  //   } else {
  //     target.next().removeClass('hidden')
  //   }
  // })
})

// function renderTemplates(template, papers){
//   var source   = $(template).html();
//   var tmpl     = Handlebars.compile(source);
//   var html     = tmpl({"papers":papers})

//   $('#papers').html(html)
// }

function setText(){
  var editor = $('#editor')
    , editorVal = editor.val()
  
  editor.parent().html(editorVal)  
}
