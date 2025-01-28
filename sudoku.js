// Sudoku solver using backtracking algorithm
function solveSudoku(board) {
    // Find empty cell
    function findEmpty(board) {
        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                if (board[row][col] === 0) {
                    return [row, col];
                }
            }
        }
        return null;
    }

    // Check if number is valid in position
    function isValid(board, num, pos) {
        // Check row
        for (let col = 0; col < 9; col++) {
            if (board[pos[0]][col] === num && col !== pos[1]) {
                return false;
            }
        }

        // Check column
        for (let row = 0; row < 9; row++) {
            if (board[row][pos[1]] === num && row !== pos[0]) {
                return false;
            }
        }

        // Check 3x3 box
        const boxRow = Math.floor(pos[0] / 3) * 3;
        const boxCol = Math.floor(pos[1] / 3) * 3;

        for (let row = boxRow; row < boxRow + 3; row++) {
            for (let col = boxCol; col < boxCol + 3; col++) {
                if (board[row][col] === num && (row !== pos[0] || col !== pos[1])) {
                    return false;
                }
            }
        }

        return true;
    }

    // Main solving function using backtracking
    function solve() {
        const empty = findEmpty(board);
        if (!empty) {
            return true; // Puzzle is solved
        }

        const [row, col] = empty;

        for (let num = 1; num <= 9; num++) {
            if (isValid(board, num, [row, col])) {
                board[row][col] = num;

                if (solve()) {
                    return true;
                }

                board[row][col] = 0; // Backtrack
            }
        }

        return false;
    }

    // Create a deep copy of the input board
    const boardCopy = board.map(row => [...row]);
    
    // Try to solve the puzzle
    if (solve()) {
        return board;
    }
    return null; // No solution exists
}

// Utility function to print the board
function printBoard(board) {
    for (let row = 0; row < 9; row++) {
        if (row % 3 === 0 && row !== 0) {
            console.log('-'.repeat(21));
        }
        let rowStr = '';
        for (let col = 0; col < 9; col++) {
            if (col % 3 === 0 && col !== 0) {
                rowStr += '| ';
            }
            rowStr += board[row][col] + ' ';
        }
        console.log(rowStr);
    }
}

// Example usage:
const exampleBoard = [
    [5,3,0,0,7,0,0,0,0],
    [6,0,0,1,9,5,0,0,0],
    [0,9,8,0,0,0,0,6,0],
    [8,0,0,0,6,0,0,0,3],
    [4,0,0,8,0,3,0,0,1],
    [7,0,0,0,2,0,0,0,6],
    [0,6,0,0,0,0,2,8,0],
    [0,0,0,4,1,9,0,0,5],
    [0,0,0,0,8,0,0,7,9]
];

console.log('Original board:');
printBoard(exampleBoard);

const solvedBoard = solveSudoku(exampleBoard);

if (solvedBoard) {
    console.log('\nSolved board:');
    printBoard(solvedBoard);
} else {
    console.log('\nNo solution exists');
}
