login_termius () {
    if [ "$SERVERAUDITOR_USERNAME" == '' ] || [ "$SERVERAUDITOR_PASSWORD" == '' ];then
      skip '$SERVERAUDITOR_USERNAME and $SERVERAUDITOR_PASSWORD are not set!'
    fi

    termius login --username $SERVERAUDITOR_USERNAME -p $SERVERAUDITOR_PASSWORD
}

pull_termius() {
    login_termius

    termius pull -p $SERVERAUDITOR_PASSWORD

}

get_models_set() {
    cat ~/.termius/storage | jq .$1
}

get_models_set_length() {
    cat ~/.termius/storage | jq ".$1 | length"
}

get_model_field() {
    instances=$(cat ~/.termius/storage | jq ".$1" | jq ".[] | select(.${4:-id} == $2)")
    echo $instances | jq ".$3"
}

clean_storage() {
    rm ~/.termius/storage
}

populate_storage() {
    termius host --address localhost
}

assert_clear_storage() {
    [ "$(get_models_set 'sshkeycrypt_set')" = "[]" ]
    [ "$(get_models_set 'tag_set')" = "[]" ]
    [ "$(get_models_set 'snippet_set')" = "[]" ]
    [ "$(get_models_set 'snippet_set')" = "[]" ]
    [ "$(get_models_set 'identity_set')" = "[]" ]
    [ "$(get_models_set 'taghost_set')" = "[]" ]
    [ "$(get_models_set 'sshconfig_set')" = "[]" ]
    [ "$(get_models_set 'group_set')" = "[]" ]
    [ "$(get_models_set 'host_set')" = "[]" ]
    [ "$(get_models_set 'pfrule_set')" = "[]" ]
}