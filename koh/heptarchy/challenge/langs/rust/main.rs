use std::io;
use std::io::Write;

fn get_player_hand(n: i8) -> i8 {
    print!("Player {} Hand [Rock/Paper/Scissors]: ", n);
    io::stdout().flush().unwrap();
    let mut hand = String::new();
    io::stdin().read_line(&mut hand).expect("I/O error");
    return match &*hand.trim().to_lowercase() {
        "rock" => 0,
        "paper" => 1,
        "scissors" => 2,
        _ => panic!("Invalid hand")
    }
}

fn main() {
    let a: i8 = get_player_hand(1);
    let b: i8 = get_player_hand(2);
    println!("{}", match a.wrapping_sub(b).rem_euclid(3) {
        0 => "Draw!",
        1 => "Player 1 wins!",
        2 => "Player 2 wins!",
        _ => unreachable!()
    });
}
